import argparse
import json
from pathlib import Path

from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler

from artifact_identity import pinned_base_path, run_identity
from experiment_config import ADAPTER, GENERATION, MODEL, ROOT, verify_test_cases
from prepare_ddxplus import decode_evidence

MAX_TOKENS = GENERATION["max_tokens"]


def read_jsonl(path):
    return [
        json.loads(line)
        for line in Path(path).read_text().splitlines()
        if line.strip()
    ]


def remove_noninitial_symptom(prompt, initial_evidence, finding=None):
    initial_text, _ = decode_evidence(initial_evidence)
    initial_bullet = f"- {initial_text}"
    lines = prompt.splitlines(keepends=True)
    section = None

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "Symptoms:":
            section = "Symptoms"
            continue
        if stripped == "Antecedents:":
            section = "Antecedents"
            continue
        if stripped and not line.startswith("- "):
            section = None

        if (
            section == "Symptoms"
            and line.startswith("- ")
            and stripped != initial_bullet
            and (finding is None or stripped[2:] == finding)
        ):
            changed_lines = lines[:index] + lines[index + 1 :]
            changed = "".join(changed_lines)
            assert changed != prompt
            assert len(lines) - len(changed_lines) == 1
            return {
                "changed_prompt": changed,
                "removed_finding": stripped[2:],
                "removed_section": section,
            }

    raise ValueError("No matching non-initial symptom available for ablation")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id")
    parser.add_argument("--finding")
    parser.add_argument("--output", default="results/counterfactual.json")
    args = parser.parse_args()
    if args.finding and not args.case_id:
        parser.error("--finding requires --case-id")
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"Ablation output already exists: {output}")

    cases = read_jsonl("evaluation/test_cases.jsonl")
    adapter_records = {
        record["case_id"]: record
        for record in read_jsonl("results/adapter.jsonl")
    }
    metadata = json.loads(Path("evaluation/metadata.json").read_text())
    adapter_run = json.loads(Path("results/adapter.run.json").read_text())
    if len(cases) != 490 or len(adapter_records) != len(cases) or adapter_run["cases"] != len(cases):
        raise ValueError("Evidence ablation requires the full 490-case adapter evaluation")
    for key, value in run_identity("adapter", MODEL, ADAPTER).items():
        if adapter_run.get(key) != value:
            raise ValueError(f"Adapter evaluation identity differs: {key}")
    test_hash = verify_test_cases()
    if adapter_run["test_cases_sha256"] != test_hash:
        raise ValueError("The adapter evaluation used a different held-out test set")

    selected = None
    ablation = None
    for case in cases:
        if args.case_id and case["case_id"] != args.case_id:
            continue
        if case["case_id"] not in adapter_records:
            continue
        try:
            candidate = remove_noninitial_symptom(
                case["prompt"],
                case["initial_evidence"],
                finding=args.finding,
            )
        except ValueError:
            continue
        if not args.case_id and not adapter_records[case["case_id"]]["structured"]:
            continue
        selected = case
        ablation = candidate
        break

    if selected is None:
        raise ValueError("No eligible held-out case found")

    original = selected["prompt"]
    changed = ablation["changed_prompt"]
    model, tokenizer = load(
        str(pinned_base_path()),
        adapter_path=str(ROOT / ADAPTER),
    )
    sampler = make_sampler(temp=0.0)
    outputs = {}

    for name, prompt_text in [
        ("original", original),
        ("one_finding_removed", changed),
    ]:
        messages = [
            {"role": "system", "content": metadata["system_prompt"]},
            {"role": "user", "content": prompt_text},
        ]
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        outputs[name] = generate(
            model,
            tokenizer,
            prompt=prompt,
            max_tokens=MAX_TOKENS,
            sampler=sampler,
            verbose=False,
        )

    saved_original = adapter_records[selected["case_id"]]["response"]
    original_matches = outputs["original"] == saved_original
    if not original_matches:
        raise ValueError("Original response differs from the full adapter evaluation")

    result = {
        "case_id": selected["case_id"],
        "source_index": selected["source_index"],
        "ground_truth_before_edit": selected["ground_truth"],
        "ground_truth_after_edit": None,
        "edited_case_has_validated_ground_truth": False,
        "initial_evidence": selected["initial_evidence"],
        "removed_finding": ablation["removed_finding"],
        "removed_section": ablation["removed_section"],
        "original_prompt": original,
        "changed_prompt": changed,
        "responses": outputs,
        "original_matches_adapter_evaluation": original_matches,
        "generation": dict(GENERATION),
        "test_cases_sha256": test_hash,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")

    print(f"Case: {selected['case_id']}")
    print(f"Removed section: {ablation['removed_section']}")
    print(f"Removed: {ablation['removed_finding']}")
    print("Original response matches full adapter evaluation: yes")
    print("\n--- ORIGINAL ---\n")
    print(outputs["original"])
    print("\n--- ONE FINDING REMOVED ---\n")
    print(outputs["one_finding_removed"])
    print("\nEvidence ablation complete; no new ground truth assigned.")


if __name__ == "__main__":
    main()
