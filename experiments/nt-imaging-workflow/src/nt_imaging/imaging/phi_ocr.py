from __future__ import annotations

import platform
from dataclasses import dataclass
from pathlib import Path

from ..constants import ALLOWED_OCR_MARKERS

OCR_ENGINE = "Apple Vision VNRecognizeTextRequest"
OCR_VERSION = "pyobjc 12.2.2"
OCR_CONFIDENCE = 0.5


class OCRError(RuntimeError):
    pass


@dataclass(frozen=True)
class OCRResult:
    verdict: str
    reasons: list[str]
    engine: str
    version: str
    language: str = "en-US"
    recognition_level: str = "accurate"
    minimum_confidence: float = OCR_CONFIDENCE


def recognize_text(path: Path) -> list[str]:
    try:
        import io

        import Vision
        from Foundation import NSData
        from PIL import Image

        with Image.open(path) as source:
            image = source.convert("RGB")
            scale = min(3.0, 1536.0 / image.width, 1536.0 / image.height)
            if scale > 1.0:
                image = image.resize(
                    (int(image.width * scale), int(image.height * scale)), Image.Resampling.NEAREST
                )
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
        raw = buffer.getvalue()
        data = NSData.dataWithBytes_length_(raw, len(raw))
        handler = Vision.VNImageRequestHandler.alloc().initWithData_options_(data, None)
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(1)
        request.setRecognitionLanguages_(["en-US"])
        request.setUsesLanguageCorrection_(False)
        request.setMinimumTextHeight_(0.01)
        success, _error = handler.performRequests_error_([request], None)
        if not success:
            raise OCRError("Local OCR recognition failed")
        observations = request.results() or []
        texts: list[str] = []
        for observation in observations:
            candidates = observation.topCandidates_(1)
            if candidates and candidates[0].confidence() >= OCR_CONFIDENCE:
                texts.append(str(candidates[0].string()))
        return texts
    except OCRError:
        raise
    except Exception as exc:
        raise OCRError("Local OCR is unavailable or could not read the image") from exc


def screen_image_text(path: Path) -> OCRResult:
    if platform.system() != "Darwin":
        raise OCRError("The baseline PHI screen requires Apple Vision on macOS")
    texts = recognize_text(path)
    unexpected = []
    for text in texts:
        normalized = " ".join(text.upper().strip().split())
        if normalized and normalized not in ALLOWED_OCR_MARKERS:
            unexpected.append(normalized)
    return OCRResult(
        verdict="BLOCKED" if unexpected else "CLEAR",
        reasons=["OCR_UNEXPECTED_TEXT"] if unexpected else [],
        engine=OCR_ENGINE,
        version=OCR_VERSION,
    )
