import argparse
import json
import os
import re
from pathlib import Path

from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler

from artifact_identity import pinned_base_path, run_identity
from experiment_config import ADAPTER as DEFAULT_ADAPTER
from experiment_config import FUSED as DEFAULT_FUSED
from experiment_config import MODEL as DEFAULT_MODEL
from experiment_config import ROOT, verify_test_cases

MODEL = os.environ.get("MODEL", DEFAULT_MODEL)
ADAPTER = os.environ.get("ADAPTER", DEFAULT_ADAPTER)
FUSED = os.environ.get("FUSED", DEFAULT_FUSED)

RESULTS = Path("results")
RESULTS.mkdir(exist_ok=True)
TEST_PATH = Path("evaluation/test_cases.jsonl")


def read_jsonl(path):
    return [
        json.loads(line)
        for line in Path(path).read_text().splitlines()
        if line.strip()
    ]


def normalize(value):
    value = value.strip().lower()
    value = re.sub(r"[*_`#]", "", value)
    value = re.sub(r"^\d+[.)]\s*", "", value)
    value = value.split("—")[0].split(" - ")[0]
    value = re.sub(r"\s+", " ", value)

    return value.strip(" .:\t")


def extract_section(text, start, end=None, inline=True):
    pattern = rf"^[ \t]*{start}[ \t]*"
    pattern += r":?[ \t]*(?:\n+|(?=\S))" if inline else r"\n+"
    pattern += r"(.+?)"

    if end:
        pattern += rf"(?=\n[ \t]*{end}[ \t]*:?|\Z)"
    else:
        pattern += r"(?=\Z)"

    match = re.search(
        pattern,
        text,
        flags=re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )

    return match.group(1).strip() if match else ""


def parse_differential(text, canonical, allow_unranked):
    differential = []

    for line in text.splitlines():
        ranked = re.match(r"^\s*(?:\d+[.)]|[-*])\s*", line)
        if ranked:
            candidates = [line]
        elif allow_unranked and line.strip():
            candidates = line.split(",")
        else:
            continue

        for candidate in candidates:
            label = canonical.get(normalize(candidate))
            if label and label not in differential:
                differential.append(label)

    return differential


def parse_response(text, conditions):
    canonical = {
        normalize(label): label
        for label in conditions
    }

    most_section = extract_section(
        text,
        "Most likely pathology",
        "Differential diagnoses",
    )
    most_line = next(
        (
            line
            for line in most_section.splitlines()
            if line.strip()
        ),
        "",
    )
    most_likely = canonical.get(normalize(most_line))

    differential_section = extract_section(
        text,
        "Differential diagnoses",
        "Uncertainty",
    )
    differential = parse_differential(
        differential_section,
        canonical,
        allow_unranked=True,
    )

    strict_most_section = extract_section(
        text,
        "Most likely pathology",
        "Differential diagnoses",
        inline=False,
    )
    strict_most_line = next(
        (
            line
            for line in strict_most_section.splitlines()
            if line.strip()
        ),
        "",
    )
    strict_most_likely = canonical.get(normalize(strict_most_line))
    strict_differential_section = extract_section(
        text,
        "Differential diagnoses",
        "Uncertainty",
        inline=False,
    )
    strict_differential = parse_differential(
        strict_differential_section,
        canonical,
        allow_unranked=False,
    )
    uncertainty = extract_section(text, "Uncertainty", inline=False)
    structured = bool(
        strict_most_likely
        and len(strict_differential) == 3
        and uncertainty
    )

    return {
        "most_likely": most_likely,
        "differential": differential[:3],
        "structured": structured,
    }


def make_summary(records, args, test_hash):
    total = len(records)
    if total == 0:
        raise ValueError("No evaluation records")

    return {
        "mode": args.mode,
        "cases": total,
        "top1_accuracy": (
            sum(r["top1"] for r in records) / total
        ),
        "top3_accuracy": (
            sum(r["top3"] for r in records) / total
        ),
        "structured_response_rate": (
            sum(r["structured"] for r in records) / total
        ),
        "mean_reference_overlap_at_3": (
            sum(r["reference_overlap"] for r in records)
            / total
        ),
        "test_cases_sha256": test_hash,
        "generation": {
            "max_tokens": args.max_tokens,
            "temperature": 0.0,
        },
    }


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["base", "adapter", "fused"],
        required=True,
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=220,
    )
    parser.add_argument("--output-prefix")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--reparse", action="store_true")

    args = parser.parse_args()
    if args.limit < 0 or args.max_tokens <= 0:
        parser.error("--limit must be nonnegative and --max-tokens must be positive")

    metadata = json.loads(
        Path("evaluation/metadata.json").read_text()
    )

    cases = read_jsonl(TEST_PATH)

    if args.limit > 0:
        cases = cases[: args.limit]

    if not cases:
        raise ValueError("No evaluation cases selected")

    test_hash = verify_test_cases(TEST_PATH)
    prefix = Path(args.output_prefix) if args.output_prefix else RESULTS / args.mode
    prefix.parent.mkdir(parents=True, exist_ok=True)
    record_path = prefix.with_suffix(".jsonl")
    summary_path = prefix.with_suffix(".summary.json")
    run_path = prefix.with_suffix(".run.json")
    selected_model = FUSED if args.mode == "fused" else MODEL
    adapter_path = ADAPTER if args.mode == "adapter" else None
    run_config = {
        "mode": args.mode,
        "cases": len(cases),
        "test_cases_sha256": test_hash,
        "max_tokens": args.max_tokens,
        "temperature": 0.0,
        **run_identity(args.mode, selected_model, adapter_path),
    }

    records = []
    if record_path.exists():
        if not args.resume:
            raise FileExistsError(
                f"{record_path} exists; use --resume to verify and reuse it"
            )
        if not run_path.exists():
            raise FileExistsError(f"Missing run metadata: {run_path}")
        saved_run = json.loads(run_path.read_text())
        if any(saved_run.get(key) != value for key, value in run_config.items()):
            raise ValueError("Existing evaluation artifact, software, or contract identity differs")
        if saved_run.get("identity_capture") not in {
            "before_generation",
            "backfilled_from_preserved_artifacts",
        }:
            raise ValueError("Existing evaluation identity provenance is unknown")
        run_config = saved_run
        records = read_jsonl(record_path)
        if len(records) > len(cases) or [
            record["case_id"] for record in records
        ] != [case["case_id"] for case in cases[: len(records)]]:
            raise ValueError("Existing evaluation records do not match the cases")
        required = {
            "response",
            "most_likely",
            "differential",
            "structured",
            "top1",
            "top3",
            "reference_overlap",
        }
        if any(not required.issubset(record) for record in records):
            raise ValueError("Existing evaluation records are incomplete")
        print(f"Reusing {len(records)} verified responses", flush=True)
    else:
        run_config["identity_capture"] = "before_generation"

    if args.reparse:
        if not record_path.exists():
            raise FileExistsError("Cannot reparse without saved responses")
        for record in records:
            parsed = parse_response(record["response"], metadata["conditions"])
            predicted = parsed["differential"]
            record.update(
                {
                    **parsed,
                    "top1": parsed["most_likely"] == record["ground_truth"],
                    "top3": record["ground_truth"] in predicted,
                    "reference_overlap": len(
                        set(predicted) & set(record["reference_top3"])
                    ),
                }
            )
        record_path.write_text(
            "".join(
                json.dumps(record, ensure_ascii=False) + "\n"
                for record in records
            )
        )
        print(f"Reparsed {len(records)} saved responses", flush=True)

    if len(records) == len(cases):
        summary = make_summary(records, args, test_hash)
        summary_path.write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary, indent=2), flush=True)
        return

    run_path.write_text(json.dumps(run_config, indent=2) + "\n")
    summary_path.unlink(missing_ok=True)
    if not records:
        record_path.write_text("")

    if args.mode == "fused":
        model, tokenizer = load(str(ROOT / FUSED))
    else:
        model, tokenizer = load(
            str(pinned_base_path()),
            adapter_path=str(ROOT / ADAPTER) if args.mode == "adapter" else None,
        )

    sampler = make_sampler(temp=0.0)

    with record_path.open("a") as output:
        for index, case in enumerate(
            cases[len(records) :],
            start=len(records) + 1,
        ):
            messages = [
                {
                    "role": "system",
                    "content": metadata["system_prompt"],
                },
                {
                    "role": "user",
                    "content": case["prompt"],
                },
            ]

            prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

            response = generate(
                model,
                tokenizer,
                prompt=prompt,
                max_tokens=args.max_tokens,
                sampler=sampler,
                verbose=False,
            )

            parsed = parse_response(
                response,
                metadata["conditions"],
            )

            predicted = parsed["differential"]

            record = {
                **case,
                "response": response,
                **parsed,
                "top1": (
                    parsed["most_likely"]
                    == case["ground_truth"]
                ),
                "top3": (
                    case["ground_truth"] in predicted
                ),
                "reference_overlap": len(
                    set(predicted)
                    & set(case["reference_top3"])
                ),
            }

            records.append(record)
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
            output.flush()

            print(
                f"[{index}/{len(cases)}] "
                f"truth={case['ground_truth']} | "
                f"predicted={parsed['most_likely']}",
                flush=True,
            )

    summary = make_summary(records, args, test_hash)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
