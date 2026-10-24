import hashlib
import importlib.metadata
import json
import platform
from functools import lru_cache
from pathlib import Path

from huggingface_hub import snapshot_download

from experiment_config import (
    ADAPTER,
    MODEL,
    MODEL_REVISION,
    ROOT,
    contract_sha256,
    file_sha256,
    local_artifact_path,
)


@lru_cache(maxsize=None)
def directory_hashes(path):
    path = Path(path)
    if not path.is_dir():
        raise FileNotFoundError(f"Artifact directory is missing: {path.name}")
    hashes = {}
    for file in sorted(path.rglob("*")):
        if not file.is_file() or file.name == ".gitattributes":
            continue
        hashes[file.relative_to(path).as_posix()] = file_sha256(file)
    if not hashes:
        raise ValueError(f"Artifact directory is empty: {path.name}")
    return hashes


def artifact_fingerprint(hashes):
    serialized = json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(serialized).hexdigest()


@lru_cache(maxsize=1)
def pinned_base_path():
    path = Path(snapshot_download(repo_id=MODEL, revision=MODEL_REVISION))
    hashes = directory_hashes(path)
    for required in ("config.json", "tokenizer.json"):
        if required not in hashes:
            raise FileNotFoundError(f"Pinned base model is missing {required}")
    index = path / "model.safetensors.index.json"
    if index.is_file():
        weight_map = json.loads(index.read_text())["weight_map"]
        missing = sorted(set(weight_map.values()) - hashes.keys())
        if missing:
            raise FileNotFoundError("Pinned base model has incomplete weight shards")
    elif "model.safetensors" not in hashes:
        raise FileNotFoundError("Pinned base model has no weights")
    return path


def runtime_versions():
    packages = (
        "mlx",
        "mlx-lm",
        "numpy",
        "pandas",
        "transformers",
        "tokenizers",
        "safetensors",
        "huggingface-hub",
    )
    return {
        "python": platform.python_version(),
        **{package: importlib.metadata.version(package) for package in packages},
    }


def evaluation_identity():
    return {
        "evaluation_code_sha256": file_sha256(ROOT / "evaluate.py"),
        "evaluation_metadata_sha256": file_sha256(ROOT / "evaluation" / "metadata.json"),
        "evaluation_contract_sha256": contract_sha256(),
    }


def run_identity(mode, model_path, adapter_path):
    if mode not in {"base", "adapter", "fused"}:
        raise ValueError(f"Unknown evaluation mode: {mode}")
    if mode == "fused":
        if adapter_path is not None:
            raise ValueError("A standalone fused evaluation must not load an adapter")
        model_files = directory_hashes(local_artifact_path(model_path))
        revision = None
    else:
        if model_path != MODEL:
            raise ValueError("The experiment requires the pinned Qwen base model")
        if mode == "adapter" and adapter_path != ADAPTER:
            raise ValueError("The experiment requires the documented adapter path")
        model_files = {
            name: digest
            for name, digest in directory_hashes(pinned_base_path()).items()
            if Path(name).suffix in {".json", ".safetensors", ".model", ".jinja", ".txt"}
        }
        revision = MODEL_REVISION
    adapter_files = (
        directory_hashes(local_artifact_path(adapter_path))
        if mode == "adapter"
        else None
    )
    return {
        "model": model_path,
        "model_revision": revision,
        "model_files_sha256": model_files,
        "adapter_files_sha256": adapter_files,
        **evaluation_identity(),
        "software": runtime_versions(),
    }
