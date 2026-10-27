from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "synthetic"


def chest_image(text: str | None = None, size: tuple[int, int] = (384, 384)) -> Image.Image:
    rng = np.random.default_rng(42)
    y, x = np.mgrid[: size[1], : size[0]]
    base = 25 + 35 * (1 - y / size[1])
    left = np.exp(
        -(
            ((x - size[0] * 0.32) / (size[0] * 0.2)) ** 2
            + ((y - size[1] * 0.53) / (size[1] * 0.34)) ** 2
        )
    )
    right = np.exp(
        -(
            ((x - size[0] * 0.68) / (size[0] * 0.2)) ** 2
            + ((y - size[1] * 0.53) / (size[1] * 0.34)) ** 2
        )
    )
    spine = np.exp(-(((x - size[0] / 2) / (size[0] * 0.045)) ** 2)) * 35
    noise = rng.normal(0, 2, (size[1], size[0]))
    pixels = np.clip(base + (left + right) * 95 + spine + noise, 0, 255).astype(np.uint8)
    image = Image.fromarray(pixels, "L").convert("RGB")
    draw = ImageDraw.Draw(image)
    draw.text((12, 12), "R", fill=(255, 255, 255))
    if text:
        draw.rectangle((45, 45, 335, 85), fill=(0, 0, 0))
        draw.text((55, 58), text, fill=(255, 255, 255))
    return image


def dicom(
    path: Path,
    *,
    modality: str = "DX",
    frames: int = 1,
    phi: bool = False,
    private: bool = False,
    text: str | None = None,
    encapsulated: bool = False,
    photometric: str = "MONOCHROME2",
    signed_voi: bool = False,
) -> None:
    image = chest_image(text)
    source_pixels = np.asarray(image.convert("L"), dtype=np.uint8)
    if signed_voi:
        pixels = (source_pixels.astype(np.int16) - 128) * 4
    elif photometric == "MONOCHROME1":
        pixels = 65535 - source_pixels.astype(np.uint16) * 257
    else:
        pixels = source_pixels

    def deterministic_uid(kind: str) -> str:
        value = int.from_bytes(hashlib.sha256(f"{path.name}:{kind}".encode()).digest()[:16], "big")
        return f"2.25.{value}"

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.1.1"
    meta.MediaStorageSOPInstanceUID = deterministic_uid("instance")
    meta.TransferSyntaxUID = "1.2.840.10008.1.2.90" if encapsulated else ExplicitVRLittleEndian
    ds = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0" * 128)
    ds.SOPClassUID = meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = deterministic_uid("study")
    ds.SeriesInstanceUID = deterministic_uid("series")
    ds.Modality = modality
    ds.Rows, ds.Columns = source_pixels.shape
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = photometric
    bits = 16 if signed_voi or photometric == "MONOCHROME1" else 8
    ds.BitsAllocated = bits
    ds.BitsStored = bits
    ds.HighBit = bits - 1
    ds.PixelRepresentation = 1 if signed_voi else 0
    if signed_voi:
        ds.RescaleSlope = 1
        ds.RescaleIntercept = 0
        ds.WindowCenter = 0
        ds.WindowWidth = 2048
    if frames > 1:
        ds.NumberOfFrames = frames
        pixels = np.stack([pixels] * frames)
    ds.PixelData = pixels.tobytes()
    if phi:
        ds.PatientName = "SYNTHETIC^PERSON"
        ds.PatientID = "SYNTHETIC-ID-001"
        ds.PatientBirthDate = "19800101"
    if private:
        ds.add_new((0x0011, 0x0010), "LO", "SYNTHETIC PRIVATE")
        ds.add_new((0x0011, 0x1001), "LO", "PRIVATE VALUE")
    ds.save_as(path, enforce_file_format=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    chest_image().save(OUT / "chest_clean.png")
    chest_image("SYNTHETIC NAME 1980-01-01").save(OUT / "chest_unexpected_text.png")
    dicom(OUT / "chest_dx.dcm")
    dicom(OUT / "chest_mono1.dcm", photometric="MONOCHROME1")
    dicom(OUT / "chest_signed_voi.dcm", signed_voi=True)
    dicom(OUT / "chest_phi.dcm", phi=True)
    dicom(OUT / "chest_private.dcm", private=True)
    dicom(OUT / "chest_burned_in.dcm", text="SYNTHETIC PATIENT 12345")
    dicom(OUT / "chest_marker.dcm")
    dicom(OUT / "unsupported_ct.dcm", modality="CT")
    dicom(OUT / "multiframe.dcm", frames=2)
    (OUT / "truncated.png").write_bytes(b"\x89PNG\r\n\x1a\ntruncated")
    (OUT / "mismatch.png").write_bytes(b"not an image")
    oversized = Image.new("RGB", (6000, 5000), (0, 0, 0))
    oversized.save(OUT / "too_many_pixels.png")
    Image.new("L", (64, 64), 0).save(OUT / "uniform.png")
    hashes = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(OUT.iterdir())
        if p.is_file()
    }
    (ROOT / "fixtures" / "expected").mkdir(parents=True, exist_ok=True)
    (ROOT / "fixtures" / "expected" / "fixture_hashes.json").write_text(
        json.dumps(hashes, indent=2) + "\n"
    )
    print(f"Generated {len(hashes)} deterministic synthetic fixtures")


if __name__ == "__main__":
    main()
