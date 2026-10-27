from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps
from pydicom.dataset import Dataset
from pydicom.pixels import apply_voi_lut  # type: ignore[attr-defined]


class RenderError(ValueError):
    pass


def render_dicom(dataset: Dataset) -> tuple[Image.Image, dict[str, Any]]:
    try:
        pixels = dataset.pixel_array
    except Exception as exc:
        raise RenderError("DICOM pixels cannot be decoded") from exc
    if pixels.ndim != 2 or dataset.get("SamplesPerPixel", 1) != 1:
        raise RenderError("Only single-frame grayscale radiographs are supported")
    if int(dataset.get("PixelRepresentation", 0)) not in {0, 1}:
        raise RenderError("Unsupported pixel representation")
    operations: list[str] = []
    if "WindowCenter" in dataset or "VOILUTSequence" in dataset:
        pixels = apply_voi_lut(pixels, dataset)
        operations.append("DICOM_VOI_LUT")
    pixels = np.asarray(pixels, dtype=np.float64)
    bits = int(dataset.get("BitsStored", 8))
    if bits not in {8, 10, 12, 16}:
        raise RenderError("Unsupported DICOM bit depth")
    if "WindowCenter" not in dataset and "VOILUTSequence" not in dataset:
        pixels = pixels * (255.0 / float((1 << bits) - 1))
        operations.append(f"BITS_STORED_{bits}_TO_8_BIT")
    else:
        low = float(np.min(pixels))
        high = float(np.max(pixels))
        if high <= low:
            pixels = np.zeros_like(pixels)
        else:
            pixels = (pixels - low) * (255.0 / (high - low))
        operations.append("POST_VOI_DISPLAY_SCALE")
    if str(dataset.get("PhotometricInterpretation", "")) == "MONOCHROME1":
        pixels = 255.0 - pixels
        operations.append("MONOCHROME1_INVERSION")
    elif str(dataset.get("PhotometricInterpretation", "")) != "MONOCHROME2":
        raise RenderError("Unsupported photometric interpretation")
    output = Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8), "L")
    return output, {"operations": operations, "bits_stored": bits}


def render_raster(path: Path) -> tuple[Image.Image, dict[str, Any]]:
    try:
        with Image.open(path) as source:
            source.load()
            image = ImageOps.exif_transpose(source).convert("L")
    except Exception as exc:
        raise RenderError("Image pixels cannot be decoded") from exc
    return image, {"operations": ["EXIF_ORIENTATION", "GRAYSCALE_8_BIT", "METADATA_REMOVED"]}


def save_png(image: Image.Image, path: Path) -> None:
    image.save(path, format="PNG", optimize=False)
