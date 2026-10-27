from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PUBLICATION_ID = "6a9439bd520526685ca0ce83"
STATE_PATH = ROOT / "docs" / "hashnode-publication.json"
DOCTOR_ID = "6adf7504d27e8100e5558907"
TITLES = {
    "doctor": "Nightthoughts Medical Imaging Workflow — Doctor and Operator User Guide",
    "installation": "Build a Local Medical Imaging Workflow with LangGraph, oMLX, and a Doctor Review Console",
}
SOURCES = {
    "doctor": ROOT / "docs" / "doctor-pipeline-user-guide.md",
    "installation": ROOT / "docs" / "installation-and-configuration.md",
}
BLOG_COPIES = {
    "doctor": ROOT / "blog" / "doctor-operator-user-guide.md",
    "installation": ROOT / "blog" / "local-langgraph-installation-guide.md",
}


def run(command: list[str], timeout: int = 120) -> dict[str, Any] | list[dict[str, Any]]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=timeout,
    )
    return json.loads(result.stdout)


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {
        "publication": "https://nightthoughts.me",
        "publication_id": PUBLICATION_ID,
        "guides": {},
    }


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")


def upload_images() -> tuple[dict[str, str], list[dict[str, Any]]]:
    files = sorted((ROOT / "docs/images/doctor-pipeline-user-guide").glob("*.png"))
    assert len(files) == 34
    uploads = run(
        ["hashnode", "--json", "image", "upload", *[str(path) for path in files]], timeout=300
    )
    assert isinstance(uploads, list) and len(uploads) == 34
    for item in uploads:
        item["file"] = Path(item["file"]).name
    by_filename = {item["file"]: item["url"] for item in uploads}
    for url in by_filename.values():
        request = urllib.request.Request(
            url,
            headers={
                "Range": "bytes=0-31",
                "User-Agent": "Nightthoughts-Guide-Verifier/1.0",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            assert response.status in {200, 206}
            assert response.headers.get("Content-Type", "").startswith("image/")
    return by_filename, uploads


def hosted_copy(name: str, urls: dict[str, str]) -> tuple[Path, int]:
    text = SOURCES[name].read_text()
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        alt, reference = match.group(1), match.group(2)
        filename = Path(reference).name
        url = urls[filename]
        width = (
            390 if filename.startswith(tuple(f"{index:02d}-" for index in range(21, 31))) else 1000
        )
        count += 1
        return f'<img src="{url}" alt="{alt}" width="{width}" />'

    hosted = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace, text)
    assert count == hosted.count("https://cdn.hashnode.com/")
    assert "images/doctor-pipeline-user-guide/" not in hosted
    assert not re.search(
        r"Bearer\s+[A-Za-z0-9_-]{12,}|__Host-nt_(session|csrf)=|BEGIN [A-Z ]*PRIVATE KEY", hosted
    )
    assert "/Users/" not in hosted
    output = ROOT / "var" / f"hashnode-{name}-guide.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(hosted)
    return output, count


def synchronize(name: str, state: dict[str, Any], urls: dict[str, str]) -> dict[str, Any]:
    source = SOURCES[name].read_bytes()
    BLOG_COPIES[name].parent.mkdir(parents=True, exist_ok=True)
    BLOG_COPIES[name].write_bytes(source)
    assert BLOG_COPIES[name].read_bytes() == SOURCES[name].read_bytes()
    content, image_count = hosted_copy(name, urls)
    entry = state["guides"].get(name, {})
    draft_id = DOCTOR_ID if name == "doctor" else entry.get("draft_id")
    subtitle = (
        "Desktop/mobile review, Imaging Readiness Agent, local graph inspection, safety scenarios, and recovery"
        if name == "doctor"
        else "Reproducible local LangGraph, deterministic image preparation, durable worker, authentication, oMLX, and evidence"
    )
    if draft_id:
        run(
            [
                "hashnode",
                "--publication-id",
                PUBLICATION_ID,
                "--json",
                "draft",
                "update",
                draft_id,
                "--title",
                TITLES[name],
                "--subtitle",
                subtitle,
                "--content-file",
                str(content),
            ]
        )
        operation = f"hashnode --publication-id {PUBLICATION_ID} --json draft update {draft_id} --content-file var/hashnode-{name}-guide.md"
    else:
        created = run(
            [
                "hashnode",
                "--publication-id",
                PUBLICATION_ID,
                "--json",
                "draft",
                "create",
                "--title",
                TITLES[name],
                "--subtitle",
                subtitle,
                "--content-file",
                str(content),
            ]
        )
        assert isinstance(created, dict) and created.get("id")
        draft_id = created["id"]
        state["guides"][name] = {"draft_id": draft_id}
        save_state(state)
        operation = f"hashnode --publication-id {PUBLICATION_ID} --json draft create --content-file var/hashnode-{name}-guide.md"
    draft = run(["hashnode", "--json", "draft", "get", draft_id])
    assert isinstance(draft, dict)
    assert draft["title"] == TITLES[name]
    body = draft["content"]["markdown"]
    assert body.count("https://cdn.hashnode.com/") == image_count
    assert "/Users/" not in body and "images/doctor-pipeline-user-guide/" not in body
    result = {
        "draft_id": draft_id,
        "title": draft["title"],
        "status": "DRAFT",
        "publicly_live": False,
        "edit_url": f"https://hashnode.com/draft/{draft_id}",
        "preview_url": f"https://nightthoughts.me/_drafts/{draft_id}",
        "preview_access": "Author authentication required; unauthenticated 404 is expected",
        "cdn_images_verified": image_count,
        "source": str(SOURCES[name].relative_to(ROOT)),
        "blog_source": str(BLOG_COPIES[name].relative_to(ROOT)),
        "upload_operation": operation,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    state["guides"][name] = result
    save_state(state)
    return result


def main(selected: str = "all") -> None:
    state = load_state()
    state["guides"].setdefault("doctor", {"draft_id": DOCTOR_ID})
    urls, uploads = upload_images()
    names = ["doctor", "installation"] if selected == "all" else [selected]
    results = [synchronize(name, state, urls) for name in names]
    evidence = {
        "publication": "https://nightthoughts.me",
        "status": "DRAFT_ONLY",
        "public_publish_command_executed": False,
        "cdn_uploads_verified": len(uploads),
        "guides": results,
    }
    output = ROOT / "evidence" / "guide" / "hashnode-v3.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2) + "\n")
    (ROOT / "evidence" / "guide" / "hashnode-images-v3.json").write_text(
        json.dumps(uploads, indent=2) + "\n"
    )
    print(json.dumps({"guides": results, "cdn_uploads_verified": len(uploads)}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "guide", choices=["doctor", "installation", "all"], default="all", nargs="?"
    )
    args = parser.parse_args()
    main(args.guide)
