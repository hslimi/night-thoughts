from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs" / "doctor-pipeline-user-guide.md"
BLOG = ROOT / "blog" / "doctor-operator-user-guide.md"
IMAGES = ROOT / "docs/images/doctor-pipeline-user-guide"
OUT = ROOT / "evidence" / "guide"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    text = GUIDE.read_text()
    assert text.startswith(
        "# Nightthoughts Medical Imaging Workflow — Doctor and Operator User Guide"
    )
    assert "Research demonstration only. Use synthetic or authorized de-identified images." in text
    assert text == BLOG.read_text()
    assert "admin/admin" not in text
    assert not re.search(
        r"Bearer\s+[A-Za-z0-9_-]{12,}|__Host-nt_(session|csrf)=|BEGIN [A-Z ]*PRIVATE KEY|/Users/",
        text,
    )
    references = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    assert len(references) == 34, f"Expected 34 image references, found {len(references)}"
    filenames = {Path(reference).name for reference in references}
    for index in range(1, 35):
        prefix = f"{index:02d}-"
        assert sum(name.startswith(prefix) for name in filenames) == 1, (
            f"Missing screenshot {prefix}"
        )
    images = []
    for reference in references:
        path = GUIDE.parent / reference
        assert path.is_file(), f"Missing image {reference}"
        with Image.open(path) as image:
            width, height = image.size
        assert height <= 900
        images.append(
            {
                "path": reference,
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
                "width": width,
                "height": height,
            }
        )
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "guide": str(GUIDE.relative_to(ROOT)),
        "blog_source": str(BLOG.relative_to(ROOT)),
        "guide_sha256": sha256(GUIDE),
        "generated_at": datetime.now(UTC).isoformat(),
        "desktop_screenshots": 20,
        "mobile_screenshots": 10,
        "additional_screenshots": 4,
        "screenshots": images,
        "responsive_results": "evidence/responsive/console-browser-tests.json",
        "capture_scope": "Actual local REAL and explicitly labelled MOCK/FAULT workflows plus public login. Chromium emulation, not physical-device testing.",
        "credentials_included": False,
    }
    (OUT / "manifest-v3.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("PASS guide structure/source sync, 34 image references/hashes, sensitive-content scan")


if __name__ == "__main__":
    main()
