import hashlib
import json
from pathlib import Path

from PIL import Image

root = Path(__file__).resolve().parent.parent
assets = root / "article" / "assets"
assets.mkdir(parents=True, exist_ok=True)
metadata = json.loads((root / "evidence" / "verification" / "ui-captures.json").read_text())

for capture in metadata["captures"]:
    name = capture["name"]
    image = Image.open(root / "evidence" / ".capture-tmp" / f"{name}.png")
    if capture["crop"]:
        box = capture["crop"]
        image = image.crop(
            (
                box["x"],
                box["y"],
                box["x"] + box["width"],
                box["y"] + box["height"],
            )
        )
    image.save(assets / f"{name}.png", optimize=True)

for source in (root / "evidence" / "workflow").glob("*.png"):
    image = Image.open(source)
    image.thumbnail((1400, 1000), Image.Resampling.LANCZOS)
    image.save(assets / source.name, optimize=True)

manifest = []
for path in sorted(assets.glob("*.png")):
    with Image.open(path) as image:
        width, height = image.size
    manifest.append(
        {
            "file": f"article/assets/{path.name}",
            "width": width,
            "height": height,
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "kind": "cover"
            if path.name == "00-cover.png"
            else (
                "application viewport"
                if path.name[:2] in {"10", "11", "12", "13", "14", "15"}
                else "VS Code window capture"
            ),
        }
    )

(root / "evidence" / "verification" / "screenshot-manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n"
)
