import argparse
import ast
import csv
import hashlib
import json
import subprocess
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd

from artifact_identity import run_identity
from evaluate import parse_response
from experiment_config import (
    EXPECTED_TEST_SHA256,
    GENERATION,
    TEST_PATH,
    verify_test_cases,
)
from make_assets import read_training_losses

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
METRICS = (
    "top1_accuracy",
    "top3_accuracy",
    "structured_response_rate",
    "mean_reference_overlap_at_3",
)


def read_json(path):
    return json.loads((ROOT / path).read_text())


def read_jsonl(path):
    return [json.loads(line) for line in (ROOT / path).read_text().splitlines()]


def write_json(path, value):
    (ROOT / path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def file_hash(path, algorithm="sha256"):
    digest = hashlib.new(algorithm)
    with (ROOT / path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_raw_data():
    checksums = {
        "release_evidences.json": "0660962abe0bbf99e1fb77188c253597",
        "release_conditions.json": "a992eadcff3099dd72e1820fbd2115aa",
        "release_train_patients.zip": "f75a78420ccb061951daa4db2d62139b",
        "release_validate_patients.zip": "e4db88e9082f18410de6fd0cb7e74d18",
        "release_test_patients.zip": "6fd53d331cf19ed4439bf4f46b92ee94",
    }
    for filename, expected in checksums.items():
        assert file_hash(Path("raw") / filename, "md5") == expected
    schema = {"AGE", "DIFFERENTIAL_DIAGNOSIS", "SEX", "PATHOLOGY", "EVIDENCES", "INITIAL_EVIDENCE"}
    expected_rows = {"train": 1_025_602, "validate": 132_448, "test": 134_529}
    row_counts = {}
    for split in ("train", "validate", "test"):
        member = f"release_{split}_patients"
        path = ROOT / "raw" / member
        with zipfile.ZipFile(ROOT / "raw" / f"{member}.zip") as archive:
            assert member in archive.namelist()
            assert Path(member).suffix == ""
            digest = hashlib.sha256()
            with archive.open(member) as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
            assert digest.hexdigest() == file_hash(Path("raw") / member)
        with path.open(newline="") as source:
            reader = csv.reader(source)
            assert set(next(reader)) == schema
            row_counts[split] = sum(1 for _ in reader)
        assert row_counts[split] == expected_rows[split]
    assert len(read_json("raw/release_evidences.json")) == 223
    assert len(read_json("raw/release_conditions.json")) == 49
    return {
        "official_md5_files_verified": 5,
        "extensionless_zip_members_verified": 3,
        "extracted_members_match_official_zip_content": True,
        "official_rows": row_counts,
        "evidence_definitions": 223,
        "pathologies": 49,
    }


def verify_source_and_splits(cases):
    from prepare_ddxplus import make_case_prompt, make_target

    metadata = read_json("evaluation/metadata.json")
    expected = {"train": 1960, "valid": 490, "test": 490}
    prompt_sets = {}
    records = {}
    for split, count in expected.items():
        records[split] = read_jsonl(f"data/{split}.jsonl")
        assert len(records[split]) == count
        for record in records[split]:
            messages = record["messages"]
            assert [message["role"] for message in messages] == ["system", "user", "assistant"]
            assert messages[0]["content"] == metadata["system_prompt"]
        prompt_sets[split] = {record["messages"][1]["content"] for record in records[split]}
        assert len(prompt_sets[split]) == count
    assert not prompt_sets["train"] & prompt_sets["valid"]
    assert not prompt_sets["train"] & prompt_sets["test"]
    assert not prompt_sets["valid"] & prompt_sets["test"]
    assert len({case["source_index"] for case in cases}) == len(cases)

    source = pd.read_csv(ROOT / "raw" / "release_test_patients")
    for case, chat in zip(cases, records["test"]):
        row = source.iloc[case["source_index"]]
        reference = ast.literal_eval(row["DIFFERENTIAL_DIAGNOSIS"])
        assert row["PATHOLOGY"] == case["ground_truth"]
        assert row["INITIAL_EVIDENCE"] == case["initial_evidence"]
        assert make_case_prompt(row) == case["prompt"] == chat["messages"][1]["content"]
        assert case["reference_top3"] == [entry[0] for entry in reference[:3]]
        assert chat["messages"][2]["content"] == make_target(row, allow_shorter=True)
    return {
        "split_counts": expected,
        "unique_prompts_per_split": True,
        "cross_split_prompt_overlap": 0,
        "official_test_rows": len(source),
        "test_prompts_and_targets_rebuilt_from_source_rows": len(cases),
    }


def verify_cases():
    cases = read_jsonl("evaluation/test_cases.jsonl")
    metadata = read_json("evaluation/metadata.json")
    labels = [case["ground_truth"] for case in cases]
    assert len(cases) == 490
    assert len({case["case_id"] for case in cases}) == 490
    assert len(metadata["conditions"]) == 49
    assert set(labels) == set(metadata["conditions"])
    assert set(Counter(labels).values()) == {10}
    digest = verify_test_cases(TEST_PATH)
    assert digest == EXPECTED_TEST_SHA256
    shorter = [case for case in cases if len(case["reference_top3"]) < 3]
    assert len(shorter) == 10
    assert {case["ground_truth"] for case in shorter} == {"Larygospasm"}
    assert all(2 <= len(case["reference_top3"]) <= 3 for case in cases)
    return cases, digest


def verify_evaluation(mode, cases, digest):
    records = read_jsonl(f"results/{mode}.jsonl")
    summary = read_json(f"results/{mode}.summary.json")
    run = read_json(f"results/{mode}.run.json")
    assert len(records) == summary["cases"] == run["cases"] == len(cases)
    assert summary["mode"] == run["mode"]
    assert summary["test_cases_sha256"] == run["test_cases_sha256"] == digest
    assert summary["generation"] == GENERATION
    assert run["max_tokens"] == GENERATION["max_tokens"]
    assert run["temperature"] == GENERATION["temperature"]
    assert run["identity_capture"] in {"before_generation", "backfilled_from_preserved_artifacts"}
    for key, value in run_identity(run["mode"], run["model"], run["adapter"]).items():
        assert run.get(key) == value, (mode, key)
    metadata = read_json("evaluation/metadata.json")
    for record, case in zip(records, cases):
        for key in ("case_id", "source_index", "initial_evidence", "prompt", "ground_truth", "reference_top3"):
            assert record[key] == case[key], (mode, record["case_id"], key)
        parsed = parse_response(record["response"], metadata["conditions"])
        assert record["most_likely"] == parsed["most_likely"]
        assert record["differential"] == parsed["differential"]
        assert record["structured"] == parsed["structured"]
        assert record["top1"] == (parsed["most_likely"] == case["ground_truth"])
        assert record["top3"] == (case["ground_truth"] in parsed["differential"])
        assert record["reference_overlap"] == len(set(parsed["differential"]) & set(case["reference_top3"]))
    calculated = {
        "top1_accuracy": sum(record["top1"] for record in records) / len(records),
        "top3_accuracy": sum(record["top3"] for record in records) / len(records),
        "structured_response_rate": sum(record["structured"] for record in records) / len(records),
        "mean_reference_overlap_at_3": sum(record["reference_overlap"] for record in records) / len(records),
    }
    for metric in METRICS:
        assert summary[metric] == calculated[metric], (mode, metric)
    return summary


def compare_modes(before_mode, after_mode):
    before = {record["case_id"]: record for record in read_jsonl(f"results/{before_mode}.jsonl")}
    after = {record["case_id"]: record for record in read_jsonl(f"results/{after_mode}.jsonl")}
    assert before.keys() == after.keys()
    return {
        "exact_response_matches": sum(before[key]["response"] == after[key]["response"] for key in before),
        "most_likely_matches": sum(before[key]["most_likely"] == after[key]["most_likely"] for key in before),
        "top1_improved_cases": sum(not before[key]["top1"] and after[key]["top1"] for key in before),
        "top1_regressed_cases": sum(before[key]["top1"] and not after[key]["top1"] for key in before),
        "most_likely_disagreements": sum(before[key]["most_likely"] != after[key]["most_likely"] for key in before),
    }


def verify_saved_comparison(filename, calculated):
    saved = read_json(filename)
    assert saved["cases"] == 490
    assert saved["test_cases_sha256"] == EXPECTED_TEST_SHA256
    for key, value in calculated.items():
        if key in saved:
            assert saved[key] == value, (filename, key)
    return saved


def verify_training():
    config = read_json("results/training-config.json")
    assert config["batch_size"] == 2
    assert config["grad_accumulation_steps"] == 4
    assert config["num_layers"] == config["lora_parameters"]["rank"] == 8
    assert config["iters"] == 1200
    assert config["learning_rate"] == 1e-5
    assert config["max_seq_length"] == 2048
    assert config["mask_prompt"] is True
    assert config["grad_checkpoint"] is True
    assert config["seed"] == 42
    train, validation = read_training_losses()
    assert train[0] == (10, 2.056)
    assert train[-1] == (1200, 0.057)
    assert validation[-1] == (1200, 0.064)
    assert (ROOT / "adapters/ddxplus/adapters.safetensors").stat().st_size > 0
    return {
        "configuration": config,
        "first_reported_training_loss": train[0][1],
        "first_reported_training_iteration": train[0][0],
        "final_training_loss": train[-1][1],
        "final_validation_loss": validation[-1][1],
        "batch_size_one_fallback_used": False,
    }


def verify_ablation():
    probe = read_json("results/counterfactual.json")
    assert probe["case_id"] == "test-0002"
    assert probe["removed_section"] == "Symptoms"
    assert probe["ground_truth_after_edit"] is None
    assert probe["edited_case_has_validated_ground_truth"] is False
    assert probe["original_matches_adapter_evaluation"] is True
    assert probe["generation"] == GENERATION
    assert probe["test_cases_sha256"] == EXPECTED_TEST_SHA256
    bullet = f"- {probe['removed_finding']}"
    assert probe["original_prompt"].replace(bullet + "\n", "", 1) == probe["changed_prompt"]
    assert bullet not in probe["changed_prompt"]
    evidences = read_json("raw/release_evidences.json")
    initial = evidences[probe["initial_evidence"]]["question_en"]
    assert f"- {initial}" in probe["original_prompt"]
    assert f"- {initial}" in probe["changed_prompt"]
    adapter = {record["case_id"]: record for record in read_jsonl("results/adapter.jsonl")}
    assert probe["responses"]["original"] == adapter[probe["case_id"]]["response"]
    return {
        "case_id": probe["case_id"],
        "removed_section": probe["removed_section"],
        "initial_evidence_preserved": True,
        "ground_truth_after_edit": None,
        "response_changed": probe["responses"]["original"] != probe["responses"]["one_finding_removed"],
    }


def verify_console():
    console = read_json("results/qwenpaw-console-verification.json")
    direct = read_json("results/omlx-verification.json")
    selected = read_json("results/omlx-selected-model.json")
    models = read_json("results/omlx-models.json")
    response = read_json("results/omlx-response.json")
    request = read_json("evaluation/omlx-request.json")
    metadata = read_json("evaluation/metadata.json")
    cases = read_jsonl("evaluation/test_cases.jsonl")
    credential = read_json("results/qwenpaw-credential-sync.json")
    case = next(case for case in cases if case["case_id"] == direct["case_id"])
    parsed = parse_response(console["response"], metadata["conditions"])
    console_matches_label = parsed["most_likely"] == case["ground_truth"]
    direct_matches = console["response"] == direct["response"]
    assert console["case_id"] == case["case_id"]
    assert console["round_trip_succeeded"] is True
    assert console["matches_dataset_label"] is console_matches_label
    assert console["matches_direct_omlx_response"] is direct_matches
    assert console["evaluation_metric"] is False
    assert console["identical_settings_benchmark"] is False
    assert console["prompt_retries_for_attractive_output"] == 0
    assert console["dataset_ground_truth"] == case["ground_truth"] == direct["ground_truth"]
    assert console["selected_model"]["model"] == selected["model_id"]
    assert file_hash("results/qwenpaw-console-message.txt") == console["prompt_sha256"]
    message = (RESULTS / "qwenpaw-console-message.txt").read_text()
    assert message == metadata["system_prompt"] + "\n\n" + case["prompt"]
    assert direct["response_model_matches_discovery"] is True
    assert direct["test_cases_sha256"] == EXPECTED_TEST_SHA256
    assert direct["model"] == selected["display_id"]
    assert direct["max_tokens"] == GENERATION["max_tokens"]
    assert direct["temperature"] == GENERATION["temperature"]
    assert selected["model_id"] in {item["id"] for item in models["data"]}
    assert response["model"] == selected["model_id"]
    assert response["choices"][0]["message"]["content"] == direct["response"]
    assert request["model"] == selected["model_id"]
    assert request["messages"] == [
        {"role": "system", "content": metadata["system_prompt"]},
        {"role": "user", "content": case["prompt"]},
    ]
    assert request["max_tokens"] == GENERATION["max_tokens"]
    assert request["temperature"] == GENERATION["temperature"]
    assert credential["status"] == "synchronized_permanently"
    assert credential["restore_original_credential_during_rollback"] is False
    assert credential["persistent_credential_matches_current_omlx"] is True
    assert credential["credential_values_recorded"] is False
    return {
        "model_discovery_and_generation_verified": True,
        "qwenpaw_round_trip_succeeded": True,
        "qwenpaw_matches_direct_omlx_response": direct_matches,
        "qwenpaw_matches_dataset_label": console_matches_label,
        "qwenpaw_top1": parsed["most_likely"],
        "qwenpaw_identical_settings_benchmark": False,
        "permanent_key_sync_requested_and_recorded": True,
    }


def verify_images():
    manifest = read_json("article-assets/manifest.json")
    hashes = {}
    assert len(manifest["images"]) == 10
    assert len({image["file"] for image in manifest["images"]}) == 10
    for image in manifest["images"]:
        data = (ROOT / image["file"]).read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        assert image["reviewed"] is True
        for source in image["sources"]:
            assert (ROOT / source).is_file(), source
        hashes[image["file"]] = hashlib.sha256(data).hexdigest()
    return hashes


def verify_rollback(required):
    path = ROOT / "results/qwenpaw-rollback.json"
    if not path.exists():
        if required:
            raise RuntimeError("Rollback has not been verified; restart QwenPaw and run its verifier")
        return {"verified": False, "status": "pending"}
    rollback = read_json("results/qwenpaw-rollback.json")
    assert rollback["configuration_backup_restored_exactly"] is True
    assert rollback["agent_backup_restored_exactly"] is True
    assert rollback["provider_connection_settings_preserved"] is True
    assert rollback["provider_model_metadata_and_removal_list_restored"] is True
    assert rollback["discovery_metadata_fields_excluded"] == [
        "capability_provenance",
        "discovered_at",
        "released_at",
    ]
    assert rollback["discovery_metadata_may_refresh"] is True
    assert rollback["global_selection_preserved"] is True
    assert rollback["actual_system_daemon_restarted_after_preparation"] is True
    assert rollback["experiment_model_registration_removed"] is True
    assert rollback["permanent_omlx_credential_sync_retained"] is True
    assert rollback["original_omlx_credential_restored"] is False
    assert rollback["adapter_and_fused_model_retained"] is True
    checkpoint = read_json("results/checkpoints/part8-rollback.json")
    assert checkpoint["status"] == "complete"
    assert checkpoint["artifact"] == "results/qwenpaw-rollback.json"
    chat = read_json("results/qwenpaw-chat-rollback.json")
    chat_checkpoint = read_json("results/checkpoints/part8-qwenpaw-chat-rollback.json")
    assert chat_checkpoint["status"] == "complete"
    assert chat_checkpoint["artifact"] == "results/qwenpaw-chat-rollback.json"
    assert chat["experiment_chat_override_restored"] is True
    assert chat["chat_history_preserved"] is True
    assert chat["new_generation_performed"] is False
    assert chat["configuration_backups_unchanged"] is True
    assert chat["restored_agent_selection"] == rollback["restored_agent_selection"]
    assert chat["global_selection_preserved"] is True
    console = read_json("results/qwenpaw-console-verification.json")
    assert chat["experiment_chat_id"] == console["final_url"].rsplit("/", 1)[-1]
    assert chat["preserved_response_case_id"] == console["case_id"]
    from qwenpaw_model import STATE_PATH, active_model, configuration_backups, file_sha256
    state = json.loads(STATE_PATH.read_text())
    assert active_model(state["agent_id"], "agent") == state["original_agent_selection"]
    assert active_model(state["agent_id"], "global") == state["original_global_selection"]
    assert chat["observed_console_default_selection"] == state["original_global_selection"]
    for destination, _, _, expected_hash in configuration_backups(state):
        assert file_sha256(destination) == expected_hash
    python = Path.home() / ".qwenpaw/venv/bin/python"
    subprocess.run(
        [str(python), str(ROOT / "qwenpaw_provider_state.py"), "--verify-current-key"],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return {
        "verified": True,
        "restored_agent_selection": rollback["restored_agent_selection"],
        "experiment_chat_override_restored": True,
        "chat_history_preserved": True,
        "permanent_omlx_credential_sync_retained": True,
        "original_omlx_credential_restored": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-rollback", action="store_true")
    args = parser.parse_args()
    raw = verify_raw_data()
    cases, digest = verify_cases()
    split_isolation = verify_source_and_splits(cases)
    summaries = {
        mode: verify_evaluation(mode, cases, digest)
        for mode in ("base", "adapter", "fused", "fused-dequantized-full")
    }
    base_adapter = compare_modes("base", "adapter")
    quantized = compare_modes("adapter", "fused")
    corrected = compare_modes("adapter", "fused-dequantized-full")
    verify_saved_comparison("results/base-adapter-comparison.json", base_adapter)
    verify_saved_comparison("results/fused-comparison.json", quantized)
    verify_saved_comparison("results/fused-dequantized-full-comparison.json", corrected)
    for filename, before_mode, after_mode in (
        ("results/base-adapter-comparison.json", "base", "adapter"),
        ("results/fused-comparison.json", "adapter", "fused"),
        ("results/fused-dequantized-full-comparison.json", "adapter", "fused-dequantized-full"),
    ):
        saved = read_json(filename)
        for metric in METRICS:
            before = summaries[before_mode][metric]
            after = summaries[after_mode][metric]
            assert saved["metrics"][metric] == {
                "before": before,
                "after": after,
                "change": after - before,
            }, (filename, metric)
    rejected = read_json("results/checkpoints/part6-quantized-verification.json")
    assert rejected["status"] == "failed"
    assert rejected["deployment_eligible"] is False
    assert quantized["exact_response_matches"] == 0
    assert quantized["most_likely_matches"] == 86
    review = read_json("results/fused-dequantized-full-deployment-review.json")
    assert review["model_path"] == "fused/ddxplus-qwen-dequantized"
    assert review["status"] == "reviewed_with_differences"
    assert review["strict_identity_gate_passed"] is False
    assert review["deployment_eligible"] is True
    assert review["review_limits"]["review_flag_supplied"] is True
    assert corrected["exact_response_matches"] == 486
    assert corrected["most_likely_matches"] == 489
    assert (490 - corrected["exact_response_matches"]) / 490 <= review["review_limits"]["maximum_response_difference_rate"]
    assert abs(summaries["fused-dequantized-full"]["top1_accuracy"] - summaries["adapter"]["top1_accuracy"]) <= review["review_limits"]["maximum_absolute_top1_accuracy_change"]
    differences = read_json(review["response_differences"])
    assert len(differences) == 4
    assert (ROOT / review["model_path"] / "config.json").is_file()
    assert (ROOT / review["model_path"] / "tokenizer.json").is_file()
    environment = read_json("results/environment.json")
    assert environment["hardware"] == "tested locally on Apple Silicon"
    rollback = verify_rollback(args.require_rollback)
    report = {
        "status": "passed" if args.require_rollback else "core_artifacts_validated",
        "dataset": raw,
        "split_isolation": split_isolation,
        "test_cases": len(cases),
        "test_labels": len({case["ground_truth"] for case in cases}),
        "test_cases_sha256": digest,
        "test_cases_with_two_reference_labels": [
            case["case_id"] for case in cases if len(case["reference_top3"]) == 2
        ],
        "generation": GENERATION,
        "summaries": summaries,
        "base_adapter_comparison": base_adapter,
        "rejected_quantized_fused_comparison": quantized,
        "dequantized_fused_comparison": corrected,
        "dequantized_fused_deployment_review": review,
        "training": verify_training(),
        "ablation": verify_ablation(),
        "deployment": verify_console(),
        "rollback": rollback,
        "software": environment,
        "image_sha256": verify_images(),
    }
    write_json("results/local-artifact-audit.json", report)
    print(f"Artifact audit: {report['status']}")
    print("Recomputed base, adapter, quantized fused, and dequantized fused metrics from all 490 saved responses.")
    print(f"Common test_cases_sha256: {digest}")
    print("Dataset checksums, training log, ablation, deployment evidence, and image provenance verified.")
    print(f"Rollback verified: {rollback['verified']}")


if __name__ == "__main__":
    main()
