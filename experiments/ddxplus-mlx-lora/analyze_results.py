import argparse
import json
from pathlib import Path

from experiment_config import EVALUATION_CASES, GENERATION, verify_test_cases

METRICS = [
    "top1_accuracy",
    "top3_accuracy",
    "structured_response_rate",
    "mean_reference_overlap_at_3",
]


def read_jsonl(path):
    return [
        json.loads(line)
        for line in Path(path).read_text().splitlines()
        if line.strip()
    ]


def load_pair(left_name, right_name):
    left_records = read_jsonl(f"results/{left_name}.jsonl")
    right_records = read_jsonl(f"results/{right_name}.jsonl")
    left_summary = json.loads(Path(f"results/{left_name}.summary.json").read_text())
    right_summary = json.loads(Path(f"results/{right_name}.summary.json").read_text())
    cases = read_jsonl("evaluation/test_cases.jsonl")
    expected_hash = verify_test_cases()

    if not len(left_records) == len(right_records) == len(cases) == EVALUATION_CASES:
        raise ValueError("Comparison requires exactly 490 records in each mode")
    if left_summary["cases"] != EVALUATION_CASES or right_summary["cases"] != EVALUATION_CASES:
        raise ValueError("Comparison summaries must cover all 490 cases")
    if left_summary["test_cases_sha256"] != expected_hash or right_summary["test_cases_sha256"] != expected_hash:
        raise ValueError("Comparison summaries use different test data")
    if left_summary["generation"] != GENERATION or right_summary["generation"] != GENERATION:
        raise ValueError("Comparison summaries use different generation settings")

    for records in (left_records, right_records):
        for record, case in zip(records, cases):
            if any(record[key] != case[key] for key in ("case_id", "prompt", "ground_truth", "reference_top3")):
                raise ValueError("Comparison responses are not aligned to the same held-out cases")

    left = {record["case_id"]: record for record in left_records}
    right = {record["case_id"]: record for record in right_records}
    if len(left) != EVALUATION_CASES or left.keys() != right.keys():
        raise ValueError("Comparison contains missing or duplicate case IDs")
    case_order = [record["case_id"] for record in left_records]

    return left, right, left_summary, right_summary, case_order, expected_hash


def comparison(left, right, left_summary, right_summary, case_order, test_hash):
    exact_matches = sum(
        left[case_id]["response"] == right[case_id]["response"]
        for case_id in case_order
    )
    prediction_matches = sum(
        left[case_id]["most_likely"] == right[case_id]["most_likely"]
        for case_id in case_order
    )
    return {
        "cases": len(case_order),
        "test_cases_sha256": test_hash,
        "exact_response_matches": exact_matches,
        "exact_response_match_rate": exact_matches / len(case_order),
        "most_likely_matches": prediction_matches,
        "most_likely_match_rate": prediction_matches / len(case_order),
        "metrics": {
            metric: {
                "before": left_summary[metric],
                "after": right_summary[metric],
                "change": right_summary[metric] - left_summary[metric],
            }
            for metric in METRICS
        },
    }


def qualitative_record(case_id, base, adapter):
    before = base[case_id]
    after = adapter[case_id]
    fields = [
        "response",
        "most_likely",
        "differential",
        "structured",
        "top1",
        "top3",
        "reference_overlap",
    ]
    return {
        "case_id": case_id,
        "source_index": after["source_index"],
        "ground_truth": after["ground_truth"],
        "reference_top3": after["reference_top3"],
        "prompt": after["prompt"],
        "base": {field: before[field] for field in fields},
        "adapter": {field: after[field] for field in fields},
    }


def analyze_base_adapter():
    base, adapter, base_summary, adapter_summary, case_order, test_hash = load_pair(
        "base", "adapter"
    )
    disagreements = []
    for case_id in case_order:
        before = base[case_id]
        after = adapter[case_id]
        if before["most_likely"] != after["most_likely"]:
            disagreements.append(
                {
                    "case_id": case_id,
                    "ground_truth": after["ground_truth"],
                    "reference_top3": after["reference_top3"],
                    "base_prediction": before["most_likely"],
                    "adapter_prediction": after["most_likely"],
                    "base_differential": before["differential"],
                    "adapter_differential": after["differential"],
                }
            )

    Path("results/disagreements.json").write_text(
        json.dumps(disagreements, indent=2, ensure_ascii=False) + "\n"
    )

    improved = next(
        (
            case_id
            for case_id in case_order
            if not base[case_id]["top1"] and adapter[case_id]["top1"]
        ),
        None,
    )
    shared_failure = next(
        (
            case_id
            for case_id in case_order
            if not base[case_id]["top1"]
            and not adapter[case_id]["top1"]
            and case_id != improved
        ),
        None,
    )
    formatted_incorrect = next(
        (
            case_id
            for case_id in case_order
            if adapter[case_id]["structured"]
            and not adapter[case_id]["top1"]
            and case_id not in {improved, shared_failure}
        ),
        None,
    )

    selected = {
        "improved": improved,
        "shared_failure": shared_failure,
        "well_formatted_incorrect": formatted_incorrect,
    }
    examples = {
        "sources": ["results/base.jsonl", "results/adapter.jsonl"],
        "test_cases_sha256": test_hash,
        "examples": {
            name: qualitative_record(case_id, base, adapter) if case_id else None
            for name, case_id in selected.items()
        },
    }
    Path("results/qualitative-examples.json").write_text(
        json.dumps(examples, indent=2, ensure_ascii=False) + "\n"
    )

    result = comparison(
        base, adapter, base_summary, adapter_summary, case_order, test_hash
    )
    result["top1_improved_cases"] = sum(
        not base[case_id]["top1"] and adapter[case_id]["top1"]
        for case_id in case_order
    )
    result["top1_regressed_cases"] = sum(
        base[case_id]["top1"] and not adapter[case_id]["top1"]
        for case_id in case_order
    )
    result["most_likely_disagreements"] = len(disagreements)
    result["qualitative_case_ids"] = selected
    Path("results/base-adapter-comparison.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def analyze_adapter_fused(fused_name):
    adapter, fused, adapter_summary, fused_summary, case_order, test_hash = load_pair(
        "adapter", fused_name
    )
    result = comparison(
        adapter, fused, adapter_summary, fused_summary, case_order, test_hash
    )
    mismatches = [
        {
            "case_id": case_id,
            "adapter_prediction": adapter[case_id]["most_likely"],
            "fused_prediction": fused[case_id]["most_likely"],
            "responses_match": (
                adapter[case_id]["response"] == fused[case_id]["response"]
            ),
        }
        for case_id in case_order
        if adapter[case_id]["response"] != fused[case_id]["response"]
        or adapter[case_id]["most_likely"] != fused[case_id]["most_likely"]
    ]
    result["response_or_prediction_mismatches"] = len(mismatches)
    Path(f"results/{fused_name}-disagreements.json").write_text(
        json.dumps(mismatches, indent=2, ensure_ascii=False) + "\n"
    )
    Path(f"results/{fused_name}-comparison.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--compare",
        choices=["base-adapter", "adapter-fused"],
        required=True,
    )
    parser.add_argument("--fused-prefix", default="fused")
    args = parser.parse_args()
    if args.compare == "base-adapter":
        analyze_base_adapter()
    else:
        analyze_adapter_fused(args.fused_prefix)


if __name__ == "__main__":
    main()
