import argparse
import ast
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from experiment_config import verify_test_cases, write_test_hash

RAW = Path("raw")
DATA = Path("data")
EVALUATION = Path("evaluation")

TRAIN_PER_CLASS = 40
EVAL_PER_CLASS = 10
SEED = 42

with (RAW / "release_evidences.json").open() as f:
    EVIDENCES = json.load(f)

with (RAW / "release_conditions.json").open() as f:
    CONDITIONS = json.load(f)

CONDITION_NAMES = sorted(CONDITIONS)

SYSTEM_PROMPT = f"""You are an educational diagnostic pattern-matching model.
Use only the supplied synthetic patient case.

Return exactly these sections:
Most likely pathology
Differential diagnoses
Uncertainty

The differential must contain exactly three ranked pathology labels.
Choose labels only from this closed set:
{', '.join(CONDITION_NAMES)}

Do not recommend treatment, investigations, or patient-specific medical care.
"""

UNCERTAINTY = (
    "This is a synthetic DDXPlus case. The output is an educational "
    "prediction, not a clinical diagnosis."
)


def decode_evidence(item):
    if "_@_" in item:
        code, value = item.split("_@_", 1)
        metadata = EVIDENCES[code]

        meaning = (
            metadata.get("value_meaning", {})
            .get(value, {})
            .get("en", value)
        )

        if meaning == "N":
            meaning = "No"

        return (
            f"{metadata['question_en']} {meaning}",
            metadata["is_antecedent"],
        )

    metadata = EVIDENCES[item]

    return (
        f"{metadata['question_en']} Yes.",
        metadata["is_antecedent"],
    )


def make_case_prompt(row):
    symptoms = []
    antecedents = []

    for item in ast.literal_eval(row["EVIDENCES"]):
        text, is_antecedent = decode_evidence(item)
        destination = antecedents if is_antecedent else symptoms
        destination.append(text)

    sex = {"M": "Male", "F": "Female"}.get(
        row["SEX"], str(row["SEX"])
    )

    sections = [
        f"Age: {row['AGE']}",
        f"Sex: {sex}",
    ]

    if symptoms:
        sections.append(
            "Symptoms:\n"
            + "\n".join(f"- {item}" for item in symptoms)
        )

    if antecedents:
        sections.append(
            "Antecedents:\n"
            + "\n".join(f"- {item}" for item in antecedents)
        )

    return (
        "Assess this synthetic patient case.\n\n"
        + "\n\n".join(sections)
    )


def make_target(row, allow_shorter=False):
    ground_truth = row["PATHOLOGY"]
    reference = ast.literal_eval(row["DIFFERENTIAL_DIAGNOSIS"])

    reference_labels = [entry[0] for entry in reference]

    ranked = [ground_truth]
    ranked.extend(
        label for label in reference_labels
        if label != ground_truth
    )
    ranked = ranked[:3]

    if len(ranked) != 3 and not (allow_shorter and ranked):
        raise ValueError("Expected three differential labels")

    differential = "\n".join(
        f"{index}. {label}"
        for index, label in enumerate(ranked, start=1)
    )

    return (
        f"Most likely pathology\n{ground_truth}\n\n"
        f"Differential diagnoses\n{differential}\n\n"
        f"Uncertainty\n{UNCERTAINTY}"
    )


def stratified_sample(df, per_class, used_prompts):
    parts = []

    for pathology, group in df.groupby("PATHOLOGY"):
        if len(group) < per_class:
            raise ValueError(
                f"{pathology}: {len(group)} eligible rows, "
                f"requested {per_class}"
            )

        initial = group.sample(n=per_class, random_state=SEED)
        remaining = group.drop(index=initial.index).sample(
            frac=1,
            random_state=SEED,
        )
        candidates = pd.concat([initial, remaining])
        selected_indices = []

        for index, row in candidates.iterrows():
            prompt = make_case_prompt(row)
            if prompt in used_prompts:
                continue
            used_prompts.add(prompt)
            selected_indices.append(index)
            if len(selected_indices) == per_class:
                break

        if len(selected_indices) != per_class:
            raise ValueError(
                f"{pathology}: insufficient unique isolated prompts"
            )

        parts.append(group.loc[selected_indices])

    return (
        pd.concat(parts)
        .sample(frac=1, random_state=SEED)
        .reset_index(drop=False)
    )


def write_jsonl(path, records):
    with path.open("w") as f:
        for record in records:
            f.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )


def process_split(
    source_name,
    output_name,
    per_class,
    used_prompts,
    is_test=False,
):
    print(f"Reading {source_name}...")

    df = pd.read_csv(RAW / source_name)

    reference_lengths = df["DIFFERENTIAL_DIAGNOSIS"].map(
        lambda value: len(ast.literal_eval(value))
    )
    eligible = reference_lengths >= 3

    if output_name in {"valid", "test"}:
        eligible |= (
            (df["PATHOLOGY"] == "Larygospasm")
            & (reference_lengths >= 2)
        )

    df = df[eligible].copy()

    subset = stratified_sample(df, per_class, used_prompts)

    chat_records = []
    evaluation_records = []

    for index, row in subset.iterrows():
        prompt = make_case_prompt(row)
        target = make_target(
            row,
            allow_shorter=output_name in {"valid", "test"},
        )

        chat_records.append(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                    {
                        "role": "assistant",
                        "content": target,
                    },
                ]
            }
        )

        if is_test:
            reference = ast.literal_eval(
                row["DIFFERENTIAL_DIAGNOSIS"]
            )

            evaluation_records.append(
                {
                    "case_id": f"test-{index:04d}",
                    "source_index": int(row["index"]),
                    "initial_evidence": row["INITIAL_EVIDENCE"],
                    "prompt": prompt,
                    "ground_truth": row["PATHOLOGY"],
                    "reference_top3": [
                        entry[0] for entry in reference[:3]
                    ],
                }
            )

    write_jsonl(
        DATA / f"{output_name}.jsonl",
        chat_records,
    )

    if is_test:
        write_jsonl(
            EVALUATION / "test_cases.jsonl",
            evaluation_records,
        )

    print(f"Wrote {len(chat_records)} {output_name} examples")


def generated_paths():
    return [
        *(DATA / f"{split}.jsonl" for split in ("train", "valid", "test")),
        EVALUATION / "test_cases.jsonl",
        EVALUATION / "test_cases.sha256",
        EVALUATION / "metadata.json",
    ]


def verify_generated_datasets():
    metadata = json.loads((EVALUATION / "metadata.json").read_text())
    expected_metadata = {
        "system_prompt": SYSTEM_PROMPT,
        "conditions": CONDITION_NAMES,
        "seed": SEED,
        "train_per_class": TRAIN_PER_CLASS,
        "evaluation_per_class": EVAL_PER_CLASS,
    }
    if metadata != expected_metadata:
        raise ValueError("Generated metadata differs from the experiment contract")

    prompt_sets = {}
    test_records = None
    for split, per_class in (
        ("train", TRAIN_PER_CLASS),
        ("valid", EVAL_PER_CLASS),
        ("test", EVAL_PER_CLASS),
    ):
        records = [
            json.loads(line)
            for line in (DATA / f"{split}.jsonl").read_text().splitlines()
            if line.strip()
        ]
        expected = per_class * len(CONDITION_NAMES)
        if len(records) != expected:
            raise ValueError(f"{split}: expected {expected} records, found {len(records)}")
        ground_truths = []
        prompts = set()
        for record in records:
            messages = record["messages"]
            if [message["role"] for message in messages] != ["system", "user", "assistant"]:
                raise ValueError(f"{split}: unexpected chat-message structure")
            if messages[0]["content"] != SYSTEM_PROMPT:
                raise ValueError(f"{split}: system prompt differs")
            prompt = messages[1]["content"]
            if prompt in prompts:
                raise ValueError(f"{split}: duplicate decoded prompt")
            prompts.add(prompt)
            target = messages[2]["content"]
            header = "Most likely pathology\n"
            if not target.startswith(header):
                raise ValueError(f"{split}: invalid target header")
            ground_truth = target[len(header):].split("\n", 1)[0]
            if ground_truth not in CONDITION_NAMES:
                raise ValueError(f"{split}: target is outside the closed label set")
            differential = target.split("\n\nDifferential diagnoses\n", 1)[1]
            ranked = differential.split("\n\nUncertainty\n", 1)[0].splitlines()
            expected_labels = {3} if split == "train" else {2, 3}
            if len(ranked) not in expected_labels:
                raise ValueError(f"{split}: unexpected target differential length")
            if any(
                not line.startswith(f"{index}. ")
                or line[len(f'{index}. '):] not in CONDITION_NAMES
                for index, line in enumerate(ranked, start=1)
            ):
                raise ValueError(f"{split}: invalid ranked target labels")
            if not target.endswith(f"\n\nUncertainty\n{UNCERTAINTY}"):
                raise ValueError(f"{split}: uncertainty contract differs")
            ground_truths.append(ground_truth)
        if Counter(ground_truths) != Counter({label: per_class for label in CONDITION_NAMES}):
            raise ValueError(f"{split}: stratified class counts differ")
        prompt_sets[split] = prompts
        if split == "test":
            test_records = records

    for left, right in (("train", "valid"), ("train", "test"), ("valid", "test")):
        if prompt_sets[left] & prompt_sets[right]:
            raise ValueError(f"Prompt leakage between {left} and {right}")

    cases = [
        json.loads(line)
        for line in (EVALUATION / "test_cases.jsonl").read_text().splitlines()
        if line.strip()
    ]
    expected_cases = EVAL_PER_CLASS * len(CONDITION_NAMES)
    if len(cases) != expected_cases or len({case["case_id"] for case in cases}) != expected_cases:
        raise ValueError("Expected 490 unique held-out cases")
    if len({case["source_index"] for case in cases}) != len(cases):
        raise ValueError("Held-out source row indices are not unique")
    for case, chat in zip(cases, test_records):
        if case["prompt"] != chat["messages"][1]["content"]:
            raise ValueError(f"{case['case_id']}: test prompt differs from chat data")
        ground_truth = chat["messages"][2]["content"][len("Most likely pathology\n"):].split("\n", 1)[0]
        if case["ground_truth"] != ground_truth:
            raise ValueError(f"{case['case_id']}: ground truth differs from chat data")
        reference = case["reference_top3"]
        if len(reference) not in {2, 3} or len(set(reference)) != len(reference):
            raise ValueError(f"{case['case_id']}: invalid reference differential")
        if any(label not in CONDITION_NAMES for label in reference):
            raise ValueError(f"{case['case_id']}: reference is outside the closed label set")
        if len(reference) == 2 and ground_truth != "Larygospasm":
            raise ValueError(f"{case['case_id']}: unexpected two-label exception")
    digest = verify_test_cases(EVALUATION / "test_cases.jsonl")
    print("Existing generated datasets verified; no files were rewritten.")
    print("Split counts: train=1960, valid=490, test=490; prompt overlap=0")
    print(f"test_cases_sha256: {digest}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite-generated",
        action="store_true",
        help="Explicitly replace generated JSONL, metadata, and test-hash files after inspection.",
    )
    args = parser.parse_args()
    DATA.mkdir(exist_ok=True)
    EVALUATION.mkdir(exist_ok=True)
    outputs = generated_paths()
    existing = [path for path in outputs if path.exists()]
    if existing and not args.overwrite_generated:
        if len(existing) != len(outputs):
            missing = [path.as_posix() for path in outputs if not path.exists()]
            raise FileExistsError(
                f"Generated data is incomplete ({', '.join(missing)} missing); "
                "inspect it before choosing --overwrite-generated."
            )
        verify_generated_datasets()
        return

    used_prompts = set()
    process_split(
        "release_train_patients",
        "train",
        TRAIN_PER_CLASS,
        used_prompts,
    )
    process_split(
        "release_validate_patients",
        "valid",
        EVAL_PER_CLASS,
        used_prompts,
    )
    process_split(
        "release_test_patients",
        "test",
        EVAL_PER_CLASS,
        used_prompts,
        is_test=True,
    )

    with (EVALUATION / "metadata.json").open("w") as f:
        json.dump(
            {
                "system_prompt": SYSTEM_PROMPT,
                "conditions": CONDITION_NAMES,
                "seed": SEED,
                "train_per_class": TRAIN_PER_CLASS,
                "evaluation_per_class": EVAL_PER_CLASS,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    write_test_hash(EVALUATION / "test_cases.jsonl")
    verify_generated_datasets()
    print("Verified the pinned 490-case test-set SHA-256 sidecar")


if __name__ == "__main__":
    main()
