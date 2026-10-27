from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, cast

import numpy as np
import pydicom
import SimpleITK as sitk
from PIL import Image
from PIL import __version__ as pillow_version
from pydicom.dataset import Dataset
from pydicom.multival import MultiValue
from pydicom.pixels import (  # type: ignore[attr-defined]
    apply_modality_lut,
    apply_voi_lut,
)

from ..artifacts import ArtifactStore, sha256_bytes, sha256_file
from ..audit import utc_now
from .dicom_io import read_dicom

CODE_VERSION = "imaging-readiness-v2"
POLICY_VERSION = "cxr-preparation-v2"


class PreparationError(ValueError):
    pass


def _policy(root: Path) -> dict[str, Any]:
    return cast(
        dict[str, Any], json.loads((root / "policies" / "cxr_preparation_v2.json").read_text())
    )


def _rescale(dataset: Dataset, pixels: np.ndarray, operations: list[str]) -> np.ndarray:
    result = apply_modality_lut(pixels, dataset)
    if "RescaleSlope" in dataset or "RescaleIntercept" in dataset:
        operations.append(
            f"MODALITY_LUT_SLOPE_{dataset.get('RescaleSlope', 1)}_INTERCEPT_{dataset.get('RescaleIntercept', 0)}"
        )
    return np.asarray(result, dtype=np.float64)


def _display_map(dataset: Dataset, pixels: np.ndarray, operations: list[str]) -> np.ndarray:
    if "VOILUTSequence" in dataset:
        operations.append("VOI_LUT_FIRST")
        if not np.all(pixels == np.rint(pixels)):
            raise PreparationError("VOI LUT input must contain integral modality values")
        pixels = np.asarray(
            apply_voi_lut(np.rint(pixels).astype(np.int64), dataset), dtype=np.float64
        )
        descriptor = dataset.VOILUTSequence[0].LUTDescriptor
        output_bits = int(descriptor[2])
        low, high = 0.0, float((1 << output_bits) - 1)
    elif "WindowCenter" in dataset and "WindowWidth" in dataset:
        operations.append("VOI_WINDOW_FIRST")
        pixels = np.asarray(apply_voi_lut(pixels, dataset), dtype=np.float64)
        center_value = dataset.WindowCenter
        width_value = dataset.WindowWidth
        center = float(center_value[0] if isinstance(center_value, MultiValue) else center_value)
        width = float(width_value[0] if isinstance(width_value, MultiValue) else width_value)
        low = center - 0.5 - (width - 1) / 2
        high = center - 0.5 + (width - 1) / 2
    else:
        signed = int(dataset.get("PixelRepresentation", 0)) == 1
        bits = int(dataset.get("BitsStored", 8))
        low = float(-(1 << (bits - 1))) if signed else 0.0
        high = float((1 << (bits - 1)) - 1) if signed else float((1 << bits) - 1)
        slope = float(dataset.get("RescaleSlope", 1))
        intercept = float(dataset.get("RescaleIntercept", 0))
        low, high = sorted((low * slope + intercept, high * slope + intercept))
        if signed:
            operations.append(f"SIGNED_THEORETICAL_SHIFT_BITS_{bits}")
        else:
            operations.append(f"UNSIGNED_THEORETICAL_RANGE_BITS_{bits}")
    if not np.isfinite(pixels).all():
        raise PreparationError("No finite pixels after VOI mapping")
    if high <= low:
        raise PreparationError("Invalid display mapping range")
    return (pixels - low) * (255.0 / (high - low))


def _resample(image: Image.Image, max_dimension: int) -> tuple[Image.Image, list[str]]:
    width, height = image.size
    largest = max(width, height)
    if largest <= max_dimension:
        return image, []
    scale = max_dimension / largest
    dimensions = (max(1, round(width * scale)), max(1, round(height * scale)))
    source = sitk.GetImageFromArray(np.asarray(image, dtype=np.float32))
    reference = sitk.Image([dimensions[0], dimensions[1]], sitk.sitkFloat32)  # type: ignore[no-untyped-call]
    spacing = (width / dimensions[0], height / dimensions[1])
    reference.SetSpacing(spacing)  # type: ignore[no-untyped-call]
    transform = sitk.Transform()  # type: ignore[no-untyped-call]
    resized = sitk.Resample(source, reference, transform, sitk.sitkBSpline, 0.0)
    return Image.fromarray(sitk.GetArrayFromImage(resized).astype(np.uint8)), [
        f"BSPLINE_ASPECT_PRESERVING_RESAMPLE_{width}x{height}_TO_{dimensions[0]}x{dimensions[1]}"
    ]


def _thumbnail(image: Image.Image, max_dimension: int) -> Image.Image:
    result = image.copy()
    result.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return result


def prepare_artifact(
    store: ArtifactStore,
    run_id: str,
    source_artifact_id: str,
    source_format: str,
    policy_root: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    policy = _policy(policy_root)
    source_path = store.derived_path(
        run_id, source_artifact_id, ".dcm" if source_format == "DICOM" else ".png"
    )
    source_hash = sha256_file(source_path)
    key_material = f"{source_hash}:{policy['policy_version']}:{CODE_VERSION}".encode()
    readiness_key = sha256_bytes(key_material)
    artifact_id = readiness_key[:32]
    prepared_path = store.derived_path(run_id, artifact_id, ".png")
    receipt_id = readiness_key[:32]
    receipt_path = store.run_dir(run_id, "runs") / f"preparation_{receipt_id}.json"
    if prepared_path.exists() and receipt_path.exists():
        receipt = cast(dict[str, Any], json.loads(receipt_path.read_text()))
        if (
            receipt.get("source_sha256") != source_hash
            or receipt.get("preparation_policy_version") != policy["policy_version"]
            or receipt.get("code_version") != CODE_VERSION
            or receipt.get("prepared_sha256") != sha256_file(prepared_path)
        ):
            raise PreparationError(
                "Readiness lineage mismatch; refusing incompatible derivative reuse"
            )
        with Image.open(prepared_path) as existing:
            existing.load()
            if existing.size != (
                receipt.get("preparation_metrics", {}).get("prepared_width"),
                receipt.get("preparation_metrics", {}).get("prepared_height"),
            ):
                raise PreparationError("Prepared derivative dimensions do not match its receipt")
        return receipt
    if source_format == "DICOM":
        dataset = read_dicom(source_path)
        pixels = dataset.pixel_array
        if pixels.ndim != 2:
            raise PreparationError("Only single-frame grayscale images are supported")
        bits = int(dataset.get("BitsStored", 8))
        if bits not in policy["allowed_bits_stored"]:
            raise PreparationError("Unsupported DICOM bit depth")
        operations: list[str] = []
        pixels = _rescale(dataset, pixels, operations)
        pixels = _display_map(dataset, pixels, operations)
        if str(dataset.get("PhotometricInterpretation", "")) == "MONOCHROME1":
            pixels = 255.0 - pixels
            operations.append("MONOCHROME1_INVERSION")
        elif str(dataset.get("PhotometricInterpretation", "")) != "MONOCHROME2":
            raise PreparationError("Unsupported photometric interpretation")
        operations.append("PRESERVE_DECODED_ORIENTATION_NO_FLIP")
        dtype = str(pixels.dtype)
        transfer_syntax = str(dataset.file_meta.TransferSyntaxUID)
        signed = bool(dataset.get("PixelRepresentation", 0))
    else:
        with Image.open(source_path) as source:
            source.load()
            image = source.convert("L")
        pixels = np.asarray(image, dtype=np.float64)
        operations = ["RASTER_GRAYSCALE_8_BIT", "PRESERVE_DECODED_ORIENTATION_NO_FLIP"]
        bits = 8
        dtype = str(pixels.dtype)
        transfer_syntax = None
        signed = False
    if pixels.size == 0 or pixels.ndim != 2:
        raise PreparationError("Image is empty or has invalid dimensions")
    height, width = pixels.shape
    if min(height, width) < 16 or max(height, width) > 10000:
        raise PreparationError("Image dimensions are outside supported bounds")
    if not np.isfinite(pixels).all():
        raise PreparationError("Image contains non-finite intensity values")
    pixels = np.clip(pixels, 0, 255).astype(np.uint8)
    image = Image.fromarray(pixels, "L")
    image, resize_operations = _resample(image, policy["max_input_dimension"])
    operations.extend(resize_operations)
    thumbnail = _thumbnail(image, policy["thumbnail_dimension"])
    prepared_pixels = np.asarray(image)
    metrics = _metrics(prepared_pixels, dtype, bits, signed)
    metrics.update(
        {
            "prepared_width": image.width,
            "prepared_height": image.height,
            "thumbnail_width": thumbnail.width,
            "thumbnail_height": thumbnail.height,
            "source_transfer_syntax": transfer_syntax,
        }
    )
    _validate_pixels(prepared_pixels, metrics)
    thumbnail_id = sha256_bytes(f"{readiness_key}:thumbnail".encode())[:32]
    thumbnail_path = store.derived_path(run_id, thumbnail_id, ".png")
    _atomic_png(image, prepared_path)
    _atomic_png(thumbnail, thumbnail_path)
    prepared_hash = sha256_file(prepared_path)
    with Image.open(prepared_path) as check:
        check.load()
        if check.size != image.size:
            raise PreparationError("Prepared image dimensions changed during encoding")
    receipt = {
        "receipt_id": receipt_id,
        "run_id": run_id,
        "thread_id": run_id,
        "source_artifact_id": source_artifact_id,
        "prepared_artifact_id": artifact_id,
        "display_thumbnail_id": thumbnail_id,
        "source_sha256": source_hash,
        "prepared_sha256": prepared_hash,
        "thumbnail_sha256": sha256_file(thumbnail_path),
        "preparation_policy_version": policy["policy_version"],
        "code_version": CODE_VERSION,
        "preparation_operations": operations,
        "preparation_metrics": metrics,
        "preparation_warnings": [],
        "timing_ms": int((time.monotonic() - started) * 1000),
        "created_at": utc_now(),
        "library_versions": {
            "pydicom": pydicom.__version__,
            "numpy": np.__version__,
            "SimpleITK": sitk.Version_VersionString(),  # type: ignore[no-untyped-call]
            "Pillow": pillow_version,
        },
        "lineage": [
            "original_upload",
            "phi_cleared_artifact",
            "prepared_model_input",
            "display_thumbnail",
        ],
    }
    _atomic_json(receipt_path, receipt)
    return receipt


def _metrics(pixels: np.ndarray, dtype: str, bits: int, signed: bool) -> dict[str, Any]:
    values = pixels.astype(np.float64)
    return {
        "dtype": dtype,
        "bits_stored": bits,
        "signed": signed,
        "intensity_min": float(values.min()),
        "intensity_max": float(values.max()),
        "intensity_p01": float(np.percentile(values, 1)),
        "intensity_p99": float(np.percentile(values, 99)),
        "black_fraction": float(np.mean(values == 0)),
        "white_fraction": float(np.mean(values == 255)),
    }


def _validate_pixels(pixels: np.ndarray, metrics: dict[str, Any]) -> None:
    if metrics["intensity_min"] == metrics["intensity_max"]:
        raise PreparationError("Image is uniformly black, white, or empty")
    if metrics["black_fraction"] > 0.995 or metrics["white_fraction"] > 0.995:
        raise PreparationError("Image is unexpectedly saturated")


def _atomic_png(image: Image.Image, path: Path) -> None:
    temporary = path.with_suffix(".tmp")
    image.save(temporary, format="PNG", optimize=False)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
