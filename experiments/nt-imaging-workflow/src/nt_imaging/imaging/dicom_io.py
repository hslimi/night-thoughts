from __future__ import annotations

from pathlib import Path

import pydicom
from pydicom.dataset import Dataset
from pydicom.errors import InvalidDicomError

from ..constants import (
    CR_IMAGE_STORAGE,
    DX_IMAGE_STORAGE,
    EXPLICIT_VR_LITTLE_ENDIAN,
    IMPLICIT_VR_LITTLE_ENDIAN,
)


class DicomValidationError(ValueError):
    pass


def read_dicom(path: Path, *, validate_scope: bool = True) -> Dataset:
    try:
        dataset = pydicom.dcmread(path, force=False, stop_before_pixels=False)
    except (InvalidDicomError, OSError, ValueError, EOFError) as exc:
        raise DicomValidationError("Malformed or unsupported DICOM input") from exc
    if not dataset.file_meta or "PixelData" not in dataset:
        raise DicomValidationError("DICOM must contain encapsulated-free pixel data")
    transfer = str(dataset.file_meta.get("TransferSyntaxUID", ""))
    if transfer not in {EXPLICIT_VR_LITTLE_ENDIAN, IMPLICIT_VR_LITTLE_ENDIAN}:
        raise DicomValidationError("Only uncompressed little-endian DICOM is supported")
    if validate_scope:
        if int(dataset.get("NumberOfFrames", 1)) != 1:
            raise DicomValidationError("Multi-frame DICOM is unsupported")
        if str(dataset.get("Modality", "")) not in {"CR", "DX"}:
            raise DicomValidationError("Only CR and DX modalities are supported")
        if str(dataset.get("SOPClassUID", "")) not in {CR_IMAGE_STORAGE, DX_IMAGE_STORAGE}:
            raise DicomValidationError("Unsupported DICOM SOP Class")
    for element in dataset:
        if element.VR == "SQ" and (element.keyword != "VOILUTSequence" or len(element.value) != 1):
            raise DicomValidationError("Only a single VOI LUT sequence is supported")
    return dataset


def looks_like_dicom(data: bytes) -> bool:
    return len(data) > 132 and data[128:132] == b"DICM"
