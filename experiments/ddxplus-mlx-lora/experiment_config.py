import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL = "mlx-community/Qwen2.5-1.5B-Instruct-4bit"
MODEL_REVISION = "8b403126fc14f14cfc99bb4cfa72ecbc129ea677"
ADAPTER = "adapters/ddxplus"
FUSED = "fused/ddxplus-qwen-dequantized"
TEST_PATH = ROOT / "evaluation" / "test_cases.jsonl"
TEST_HASH_PATH = TEST_PATH.with_suffix(".sha256")
EXPECTED_TEST_SHA256 = "c5a5b94a3377c78b2ac1209899ca6e8d1df3a9aa25ce0a2e26ad33373f6c5838"
EVALUATION_CASES = 490
GENERATION = {"max_tokens": 220, "temperature": 0.0}
EVALUATION_CONTRACT = {
    "version": 1,
    "chat_template": True,
    "add_generation_prompt": True,
    "response_parser": "closed-set exact labels; strict three-item structured-response flag",
    "top1": "parsed most-likely label equals the dataset pathology",
    "top3": "dataset pathology occurs in the first three unique differential labels",
    "reference_overlap_at_3": "intersection of predicted and reference differential labels",
}


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def contract_sha256():
    serialized = json.dumps(
        EVALUATION_CONTRACT,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(serialized).hexdigest()


def write_test_hash(path=TEST_PATH):
    path = Path(path)
    actual = file_sha256(path)
    if actual != EXPECTED_TEST_SHA256:
        raise ValueError("Generated test cases differ from the pinned experiment test set")
    sidecar = path.with_suffix(".sha256")
    sidecar.write_text(f"{actual}  {path.name}\n")
    verify_test_cases(path, sidecar)


def verify_test_cases(path=TEST_PATH, sidecar_path=None):
    path = Path(path)
    sidecar = Path(sidecar_path) if sidecar_path else path.with_suffix(".sha256")
    if not path.is_file() or not sidecar.is_file():
        raise FileNotFoundError("The held-out test set and its SHA-256 sidecar are required")
    fields = sidecar.read_text().split()
    if len(fields) != 2 or fields[1] != path.name:
        raise ValueError("Invalid test-set SHA-256 sidecar")
    actual = file_sha256(path)
    if actual != fields[0] or actual != EXPECTED_TEST_SHA256:
        raise ValueError("The held-out test file does not match the pinned experiment hash")
    return actual


def local_artifact_path(value):
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Use a project-relative model or adapter path")
    resolved = ROOT / path
    if not resolved.is_dir():
        raise FileNotFoundError(f"Missing local model or adapter directory: {path}")
    return resolved
