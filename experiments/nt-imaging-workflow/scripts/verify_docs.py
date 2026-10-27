from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    files = [ROOT / "README.md", *ROOT.glob("docs/*.md"), *ROOT.glob("blog/*.md")]
    checked = 0
    for source in files:
        text = source.read_text()
        for match in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", text):
            target = match.group(1).split("#", 1)[0]
            if not target or target.startswith(("https://", "http://", "mailto:")):
                continue
            path = (source.parent / target).resolve()
            assert path.exists(), f"Broken link in {source.relative_to(ROOT)}: {target}"
            checked += 1
    print(f"PASS {checked} relative documentation links and image references")


if __name__ == "__main__":
    main()
