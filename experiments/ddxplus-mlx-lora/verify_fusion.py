import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from analyze_results import comparison, load_pair
from artifact_identity import artifact_fingerprint, run_identity
from experiment_config import ADAPTER, EVALUATION_CASES, FUSED, GENERATION, MODEL, verify_test_cases

RESULTS = Path("results")
MAX_REVIEWED_RESPONSE_DIFFERENCE_RATE = 0.02
MAX_REVIEWED_TOP1_CHANGE = 0.01


def validate_run(prefix, mode, model, adapter):
    prefix = RESULTS / prefix
    run = json.loads(prefix.with_suffix(".run.json").read_text())
    summary = json.loads(prefix.with_suffix(".summary.json").read_text())
    if run["mode"] != mode or summary["mode"] != mode:
        raise ValueError(f"{prefix} is not a {mode} evaluation")
    if run["model"] != model or run["adapter"] != adapter:
        raise ValueError(f"{prefix} uses a different model or adapter")
    if run["cases"] != EVALUATION_CASES or summary["cases"] != EVALUATION_CASES:
        raise ValueError("Fusion verification requires all 490 held-out cases")
    if run["test_cases_sha256"] != verify_test_cases() or summary["test_cases_sha256"] != verify_test_cases():
        raise ValueError("Fusion verification test-set hashes differ")
    if run["max_tokens"] != GENERATION["max_tokens"] or run["temperature"] != GENERATION["temperature"]:
        raise ValueError("Fusion verification generation settings differ")
    if summary["generation"] != GENERATION:
        raise ValueError("Fusion verification summary generation settings differ")
    if run.get("identity_capture") not in {"before_generation", "backfilled_from_preserved_artifacts"}:
        raise ValueError("Fusion verification identity provenance is unknown")
    for key, value in run_identity(mode, model, adapter).items():
        if run.get(key) != value:
            raise ValueError(f"Fusion verification artifact or runtime identity differs: {key}")
    return run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fused-prefix", default="fused-dequantized-full")
    parser.add_argument("--model-path", default=FUSED)
    parser.add_argument("--accept-reviewed-differences", action="store_true")
    args = parser.parse_args()
    if Path(args.fused_prefix).name != args.fused_prefix:
        parser.error("--fused-prefix must be a filename prefix inside results/")

    adapter_run = validate_run("adapter", "adapter", MODEL, ADAPTER)
    fused_run = validate_run(args.fused_prefix, "fused", args.model_path, None)
    adapter, fused, adapter_summary, fused_summary, case_order, test_hash = load_pair(
        "adapter", args.fused_prefix
    )
    result = comparison(
        adapter, fused, adapter_summary, fused_summary, case_order, test_hash
    )
    differences = []
    for case_id in case_order:
        before = adapter[case_id]
        after = fused[case_id]
        if before["response"] == after["response"]:
            continue
        differences.append(
            {
                "case_id": case_id,
                "source_index": before["source_index"],
                "ground_truth": before["ground_truth"],
                "adapter": {
                    key: before[key]
                    for key in [
                        "most_likely",
                        "differential",
                        "top1",
                        "top3",
                        "structured",
                        "response",
                    ]
                },
                "fused": {
                    key: after[key]
                    for key in [
                        "most_likely",
                        "differential",
                        "top1",
                        "top3",
                        "structured",
                        "response",
                    ]
                },
            }
        )

    difference_path = RESULTS / f"{args.fused_prefix}-response-differences.json"
    difference_path.write_text(
        json.dumps(differences, indent=2, ensure_ascii=False) + "\n"
    )
    difference_rate = len(differences) / len(case_order)
    top1_change = abs(result["metrics"]["top1_accuracy"]["change"])
    strict_identity = not differences
    reviewed = strict_identity or (
        args.accept_reviewed_differences
        and difference_rate <= MAX_REVIEWED_RESPONSE_DIFFERENCE_RATE
        and top1_change <= MAX_REVIEWED_TOP1_CHANGE
    )
    status = (
        "exact_match"
        if strict_identity
        else "reviewed_with_differences"
        if reviewed
        else "failed"
    )
    result.update(
        {
            "model_path": args.model_path,
            "base_model_revision": adapter_run["model_revision"],
            "adapter_artifact_sha256": artifact_fingerprint(adapter_run["adapter_files_sha256"]),
            "fused_artifact_sha256": artifact_fingerprint(fused_run["model_files_sha256"]),
            "evaluation_identity_verified": True,
            "status": status,
            "strict_identity_gate_passed": strict_identity,
            "deployment_eligible": reviewed,
            "response_difference_count": len(differences),
            "response_difference_rate": difference_rate,
            "response_differences": difference_path.as_posix(),
            "review_limits": {
                "maximum_response_difference_rate": MAX_REVIEWED_RESPONSE_DIFFERENCE_RATE,
                "maximum_absolute_top1_accuracy_change": MAX_REVIEWED_TOP1_CHANGE,
                "review_flag_supplied": args.accept_reviewed_differences,
            },
            "caveat": "Reviewed numerical differences are not exact equivalence or clinical validation.",
        }
    )
    comparison_path = RESULTS / f"{args.fused_prefix}-deployment-review.json"
    comparison_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    checkpoint = {
        "stage": "part6-fused-deployment-review",
        "status": status,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "model": args.model_path,
        "artifact": comparison_path.as_posix(),
        "test_cases_sha256": test_hash,
        "strict_identity_gate_passed": strict_identity,
        "deployment_eligible": reviewed,
        "response_difference_count": len(differences),
    }
    checkpoint_path = RESULTS / "checkpoints" / "part6-fused-deployment-review.json"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not reviewed:
        raise SystemExit("Fused deployment remains blocked; inspect the saved response differences.")
    print(f"Deployment review: {status}; strict identity: {strict_identity}")


if __name__ == "__main__":
    main()
