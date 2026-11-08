import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

import torch
from unsloth import FastLanguageModel

from incident_contract import (
    ACTIONS,
    CATEGORIES,
    SERVICES,
    SEVERITIES,
    TARGET_FIELDS,
    prompt_messages,
)

BASE_MODEL = "unsloth/Qwen2.5-1.5B-Instruct"
MAX_SEQ_LENGTH = 1024
EVAL_PER_SCENARIO = 8

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["base", "finetuned"], required=True)
args = parser.parse_args()

PROJECT_DIR = Path(os.environ.get(
    "INCIDENT_TRIAGE_PROJECT_DIR",
    "/content/drive/MyDrive/nightthoughts-incident-triage",
))
DATA_DIR = PROJECT_DIR / "data"
RESULTS_DIR = PROJECT_DIR / "results"
ADAPTER_DIR = PROJECT_DIR / "adapter"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

model_name = BASE_MODEL if args.mode == "base" else str(ADAPTER_DIR)
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_name,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=True,
)
FastLanguageModel.for_inference(model)


def generate_answer(alert, max_new_tokens=180):
    inputs = tokenizer.apply_chat_template(
        prompt_messages(alert),
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    ).to("cuda")

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            use_cache=True,
        )

    generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()


def validate_prediction(text):
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None, False, False

    json_valid = True

    if not isinstance(value, dict) or set(value) != set(TARGET_FIELDS):
        return value, json_valid, False
    if value["service"] not in SERVICES:
        return value, json_valid, False
    if value["severity"] not in SEVERITIES:
        return value, json_valid, False
    if value["category"] not in CATEGORIES:
        return value, json_valid, False
    if value["next_action"] not in ACTIONS:
        return value, json_valid, False
    if not isinstance(value["summary"], str) or not value["summary"].strip():
        return value, json_valid, False
    if type(value["escalate"]) is not bool:
        return value, json_valid, False

    return value, json_valid, True


def evaluate_model(items, mode):
    predictions = []

    for index, record in enumerate(items, start=1):
        raw_output = generate_answer(record["alert"])
        parsed, json_valid, schema_valid = validate_prediction(raw_output)
        target = json.loads(record["target"])

        row = {
            "mode": mode,
            "scenario_id": record["scenario_id"],
            "alert": record["alert"],
            "raw_output": raw_output,
            "prediction": parsed,
            "target": target,
            "json_valid": json_valid,
            "schema_valid": schema_valid,
            "exact_match": schema_valid and parsed == target,
        }

        for field in TARGET_FIELDS:
            row[f"{field}_correct"] = bool(
                schema_valid and parsed[field] == target[field]
            )

        predictions.append(row)
        print(f"\r{mode}: {index}/{len(items)}", end="")

    print()
    return predictions


def summarize_predictions(predictions):
    total = len(predictions)
    metrics = {
        "cases": total,
        "json_valid_rate": sum(p["json_valid"] for p in predictions) / total,
        "schema_valid_rate": sum(p["schema_valid"] for p in predictions) / total,
        "exact_match_rate": sum(p["exact_match"] for p in predictions) / total,
    }

    for field in TARGET_FIELDS:
        metrics[f"{field}_accuracy"] = sum(
            p[f"{field}_correct"] for p in predictions
        ) / total

    unknown_cases = [p for p in predictions if p["target"]["category"] == "unknown"]
    metrics["unknown_category_recall"] = sum(
        p["schema_valid"] and p["prediction"]["category"] == "unknown"
        for p in unknown_cases
    ) / len(unknown_cases)

    return metrics


test_records = [
    json.loads(line)
    for line in (DATA_DIR / "test.jsonl").read_text(encoding="utf-8").splitlines()
]
by_scenario = defaultdict(list)
for record in test_records:
    by_scenario[record["scenario_id"]].append(record)

eval_records = []
for scenario_id in sorted(by_scenario):
    eval_records.extend(by_scenario[scenario_id][:EVAL_PER_SCENARIO])
assert len(eval_records) == 40

predictions = evaluate_model(eval_records, mode=args.mode)
metrics = summarize_predictions(predictions)

with (RESULTS_DIR / f"{args.mode}_predictions.json").open("w", encoding="utf-8") as handle:
    json.dump(predictions, handle, ensure_ascii=False, indent=2)
with (RESULTS_DIR / f"{args.mode}_metrics.json").open("w", encoding="utf-8") as handle:
    json.dump(metrics, handle, indent=2)

print(json.dumps(metrics, indent=2))
print("Evaluation scenarios:", sorted(by_scenario))
print("Evaluation cases:", len(eval_records))
