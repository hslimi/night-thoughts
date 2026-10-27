from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from .artifacts import ArtifactStore
from .config import ConfigurationError, Settings, get_omlx_api_key
from .graph import build_graph
from .state import initial_state


def run_local(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    settings.ensure_directories()
    source = Path(args.source).resolve()
    state = initial_state(
        str(source),
        inference_mode=settings.inference_mode,
        workflow_version=settings.workflow_version,
        max_attempts=settings.max_attempts,
        max_total_model_calls=settings.max_total_model_calls,
        fault_profile=args.fault_profile,
        declared_modality=args.modality,
        vision_model_id=settings.vision_model,
        text_model_id=settings.text_model,
    )
    checkpoint = settings.data_root / "checkpoints.sqlite3"
    with SqliteSaver.from_conn_string(str(checkpoint)) as saver:
        app = build_graph(saver)
        result = app.invoke(state, config={"configurable": {"thread_id": state["thread_id"]}})
        if args.decision and "__interrupt__" in result:
            result = app.invoke(
                Command(
                    resume={
                        "decision": args.decision,
                        "reviewer_display_name": args.reviewer,
                        "note": args.note,
                    }
                ),
                config={"configurable": {"thread_id": state["thread_id"]}},
            )
    manifest_path = (
        ArtifactStore(settings.data_root).run_dir(state["run_id"], "runs") / "run_manifest.json"
    )
    manifest = safe_summary(result)
    ArtifactStore(settings.data_root).write_json(manifest_path, manifest)
    print(json.dumps(manifest, indent=2))
    return (
        0
        if result.get("status")
        in {"APPROVED_DRAFT_EXPORTED", "HUMAN_REJECTED", "NEEDS_HUMAN_REVIEW", "QUARANTINED"}
        or "__interrupt__" in result
        else 1
    )


def resume_local(args: argparse.Namespace) -> int:
    settings = Settings.from_env()
    with SqliteSaver.from_conn_string(str(settings.data_root / "checkpoints.sqlite3")) as saver:
        app = build_graph(saver)
        config = {"configurable": {"thread_id": args.thread_id}}
        result = app.invoke(
            Command(
                resume={
                    "decision": args.decision,
                    "reviewer_display_name": args.reviewer,
                    "note": args.note,
                }
            ),
            config=config,
        )
    print(json.dumps(safe_summary(result), indent=2))
    return 0


def safe_summary(result: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "run_id",
        "thread_id",
        "status",
        "inference_mode",
        "fault_profile",
        "attempt",
        "model_calls",
        "phi_status",
        "phi_reasons",
        "modality_status",
        "contract_status",
        "grounding_status",
        "quality_status",
        "source_sha256",
        "prepared_sha256",
        "readiness_status",
        "readiness_receipt_id",
        "preparation_policy_version",
        "derived_phi_status",
        "vision_model_id",
        "text_model_id",
        "export_manifest",
        "error",
    ]
    summary = {key: result.get(key) for key in keys}
    if "__interrupt__" in result:
        summary["interrupt"] = result["__interrupt__"][0].value
    return summary


def doctor(_: argparse.Namespace) -> int:
    settings = Settings.from_env()
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
        if not ok:
            failures.append(name)

    check(
        "Platform",
        platform.system() == "Darwin" and platform.machine() == "arm64",
        f"{platform.system()} {platform.machine()} {platform.mac_ver()[0]}",
    )
    check("Python", sys.version_info[:2] in {(3, 11), (3, 12)}, platform.python_version())
    check(
        "Isolated environment",
        ".venv" in sys.prefix
        and ".mlx-venv" not in sys.prefix
        and "qwenpaw" not in sys.prefix.lower(),
        "repository-local environment" if ".venv" in sys.prefix else "wrong environment",
    )
    print("INFO Observability: local checkpoints, audit events, and inspector only")
    print(f"INFO Inference mode: {settings.inference_mode}")
    settings.ensure_directories()
    check("Data directories", os.access(settings.data_root, os.W_OK))
    for service in ("com.omlx.server", "com.qwenpaw.app"):
        result = subprocess.run(
            ["launchctl", "print", f"system/{service}"], check=False, capture_output=True, timeout=5
        )
        check(
            f"Existing {service}",
            result.returncode == 0,
            "present; not modified" if result.returncode == 0 else "not loaded",
        )
    for port in (8000, 8088, 9080):
        check(
            f"Existing listener {port}",
            _port_open(port),
            "reachable" if _port_open(port) else "not reachable",
        )
    for port in (8001,):
        print(f"INFO Project listener {port}: {'available' if _port_open(port) else 'not running'}")
    memory = subprocess.run(
        ["memory_pressure"], check=False, capture_output=True, text=True, timeout=10
    )
    free = next(
        (line.strip() for line in memory.stdout.splitlines() if "free percentage" in line),
        "unavailable",
    )
    print(f"INFO Memory pressure: {free}; informational only")
    if settings.inference_mode == "MOCK":
        print("MOCK / SYNTHETIC TEST MODE — real model checks intentionally not run")
    else:
        try:
            headers = {"Authorization": f"Bearer {get_omlx_api_key()}"}
            response = httpx.get(f"{settings.omlx_base_url}/models", headers=headers, timeout=10)
            response.raise_for_status()
            ids = [item["id"] for item in response.json()["data"]]
            check("oMLX authenticated inventory", True, f"{len(ids)} models")
            check(
                "Selected vision model",
                settings.vision_model in ids,
                settings.vision_model or "unset",
            )
            check("Selected text model", settings.text_model in ids, settings.text_model or "unset")
            from .inference.omlx import OMLXProvider

            provider = OMLXProvider(settings)
            text = provider._call(
                settings.text_model or "",
                [{"role": "user", "content": 'Return only JSON {"ok":true}'}],
                30,
            )
            check(
                "Minimal text inference",
                '"ok"' in text.raw,
                f"{text.model_id}, {text.latency_ms} ms",
            )
            tiny = settings.data_root / "artifacts" / "doctor_tiny.png"
            from PIL import Image

            Image.new("L", (64, 64), 127).save(tiny)
            vision = provider._call(
                settings.vision_model or "",
                provider._vision_messages(
                    "Describe this tiny synthetic gray test image in JSON with key description.",
                    tiny,
                ),
                100,
            )
            check(
                "Minimal vision inference",
                bool(vision.raw),
                f"{vision.model_id}, {vision.latency_ms} ms",
            )
        except Exception as exc:  # noqa: BLE001 - doctor converts all capability failures to a non-zero result
            check(
                "Real oMLX inference",
                False,
                f"{type(exc).__name__}; verify service, key, exact model IDs, and loaded model capacity",
            )
    try:
        from .imaging.phi_ocr import recognize_text

        recognize_text(Path("fixtures/synthetic/chest_clean.png"))
        check("Apple Vision OCR", True, "local synthetic image processed")
    except Exception as exc:  # noqa: BLE001 - doctor converts all capability failures to a non-zero result
        check("Apple Vision OCR", False, type(exc).__name__)
    return 1 if failures else 0


def _port_open(port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.3)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="nt-imaging")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("source")
    run.add_argument("--modality", choices=["XR"], default="XR")
    run.add_argument("--decision", choices=["APPROVE", "REJECT"])
    run.add_argument("--reviewer", default="Demo Reviewer")
    run.add_argument("--note", default="")
    run.add_argument("--fault-profile", default="none")
    run.set_defaults(func=run_local)
    resume = sub.add_parser("resume")
    resume.add_argument("thread_id")
    resume.add_argument("--decision", choices=["APPROVE", "REJECT"], required=True)
    resume.add_argument("--reviewer", default="Demo Reviewer")
    resume.add_argument("--note", default="")
    resume.set_defaults(func=resume_local)
    doc = sub.add_parser("doctor")
    doc.set_defaults(func=doctor)
    args = parser.parse_args()
    try:
        raise SystemExit(args.func(args))
    except (ConfigurationError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
