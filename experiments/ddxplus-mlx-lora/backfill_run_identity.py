import json
from datetime import datetime, timezone
from pathlib import Path

from artifact_identity import pinned_base_path, run_identity
from evaluate import parse_response, read_jsonl
from experiment_config import (
    ADAPTER,
    EVALUATION_CASES,
    FUSED,
    GENERATION,
    MODEL,
    ROOT,
    local_artifact_path,
    verify_test_cases,
    write_test_hash,
)

PREFIXES = {
    "base": ("base", MODEL, None),
    "adapter": ("adapter", MODEL, ADAPTER),
    "fused": ("fused", "fused/ddxplus-qwen", None),
    "fused-dequantized-full": ("fused", FUSED, None),
}
LEGACY_KEYS = {
    "mode",
    "model",
    "adapter",
    "cases",
    "test_cases_sha256",
    "max_tokens",
    "temperature",
}
METRICS = (
    "top1_accuracy",
    "top3_accuracy",
    "structured_response_rate",
    "mean_reference_overlap_at_3",
)


def verify_preserved_evaluation(prefix, mode, model, adapter, cases, metadata):
    results = ROOT / "results"
    run_path = results / f"{prefix}.run.json"
    summary_path = results / f"{prefix}.summary.json"
    record_path = results / f"{prefix}.jsonl"
    run = json.loads(run_path.read_text())
    summary = json.loads(summary_path.read_text())
    records = read_jsonl(record_path)
    expected = {
        "mode": mode,
        "model": model,
        "adapter": adapter,
        "cases": EVALUATION_CASES,
        "test_cases_sha256": verify_test_cases(),
        **GENERATION,
    }
    if set(run) != LEGACY_KEYS or run != expected:
        raise ValueError(f"Unexpected legacy run metadata for {prefix}")
    if summary["cases"] != EVALUATION_CASES or len(records) != EVALUATION_CASES:
        raise ValueError(f"Incomplete preserved evaluation: {prefix}")
    if summary["test_cases_sha256"] != verify_test_cases() or summary["generation"] != GENERATION:
        raise ValueError(f"Preserved evaluation settings differ: {prefix}")
    for record, case in zip(records, cases):
        for key in ("case_id", "source_index", "initial_evidence", "prompt", "ground_truth", "reference_top3"):
            if record[key] != case[key]:
                raise ValueError(f"Preserved cases are misaligned: {prefix}")
        parsed = parse_response(record["response"], metadata["conditions"])
        expected_flags = {
            **parsed,
            "top1": parsed["most_likely"] == case["ground_truth"],
            "top3": case["ground_truth"] in parsed["differential"],
            "reference_overlap": len(set(parsed["differential"]) & set(case["reference_top3"])),
        }
        if any(record[key] != value for key, value in expected_flags.items()):
            raise ValueError(f"Saved response parsing differs: {prefix} / {case['case_id']}")
    calculated = {
        "top1_accuracy": sum(record["top1"] for record in records) / EVALUATION_CASES,
        "top3_accuracy": sum(record["top3"] for record in records) / EVALUATION_CASES,
        "structured_response_rate": sum(record["structured"] for record in records) / EVALUATION_CASES,
        "mean_reference_overlap_at_3": sum(record["reference_overlap"] for record in records) / EVALUATION_CASES,
    }
    if any(summary[key] != calculated[key] for key in METRICS):
        raise ValueError(f"Preserved metrics differ from saved responses: {prefix}")

    identity = run_identity(mode, model, adapter)
    artifacts = [
        (
            local_artifact_path(model) if mode == "fused" else pinned_base_path(),
            identity["model_files_sha256"],
        )
    ]
    if adapter:
        artifacts.append((local_artifact_path(adapter), identity["adapter_files_sha256"]))
    latest_artifact_modification = max(
        (artifact / name).stat().st_mtime
        for artifact, hashes in artifacts
        for name in hashes
    )
    if latest_artifact_modification > record_path.stat().st_mtime:
        raise ValueError(f"An inference artifact changed after its evaluation: {prefix}")
    run.update(identity)
    run["identity_capture"] = "backfilled_from_preserved_artifacts"
    run["identity_backfill"] = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "artifact_modification_precedes_saved_evaluation": True,
        "all_saved_responses_reparsed_without_regeneration": True,
        "not_captured_during_original_generation": True,
    }
    return run_path, run, summary


def main():
    test_path = ROOT / "evaluation" / "test_cases.jsonl"
    if not test_path.with_suffix(".sha256").exists():
        write_test_hash(test_path)
    cases = read_jsonl(test_path)
    if len(cases) != EVALUATION_CASES or len({case["case_id"] for case in cases}) != EVALUATION_CASES:
        raise ValueError("The preserved test set must contain 490 unique cases")
    metadata = json.loads((ROOT / "evaluation" / "metadata.json").read_text())
    if len(metadata["conditions"]) != 49 or {case["ground_truth"] for case in cases} != set(metadata["conditions"]):
        raise ValueError("The preserved test set does not cover the 49-label closed set")
    backup = ROOT / "results" / "logs" / "identity-backfill"
    backup.mkdir(parents=True, exist_ok=True)
    for prefix, (mode, model, adapter) in PREFIXES.items():
        run_path, run, summary = verify_preserved_evaluation(prefix, mode, model, adapter, cases, metadata)
        (backup / f"{prefix}.run.before.json").write_text(run_path.read_text())
        run_path.write_text(json.dumps(run, indent=2) + "\n")
        print(f"Verified and backfilled {prefix}: {summary['cases']} preserved responses; no generation performed")


if __name__ == "__main__":
    main()
