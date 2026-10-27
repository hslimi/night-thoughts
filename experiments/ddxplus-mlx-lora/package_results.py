import hashlib
import json
import subprocess
from pathlib import Path

from experiment_config import (
    EXPECTED_TEST_SHA256,
    GENERATION,
    MODEL_REVISION,
    ROOT,
    file_sha256,
    verify_test_cases,
)

RESULTS = ROOT / "results"
PUBLIC = RESULTS / "public"
METRICS = (
    "top1_accuracy",
    "top3_accuracy",
    "structured_response_rate",
    "mean_reference_overlap_at_3",
)
SUMMARY_FILES = {
    "base.summary.json": "base.summary.json",
    "adapter.summary.json": "adapter.summary.json",
    "fused-dequantized.summary.json": "fused-dequantized-full.summary.json",
    "fused-quantized-rejected.summary.json": "fused.summary.json",
}
COPY_FILES = {
    "training-config.json": "training-config.json",
    "training-losses.json": "training-losses.json",
    "base-adapter-comparison.json": "base-adapter-comparison.json",
    "adapter-fused-dequantized-comparison.json": "fused-dequantized-full-comparison.json",
    "adapter-fused-quantized-rejected-comparison.json": "fused-comparison.json",
    "qualitative-examples.json": "qualitative-examples.json",
    "evidence-ablation.json": "counterfactual.json",
    "fused-response-differences.json": "fused-dequantized-full-response-differences.json",
}
SOURCE_FILES = [
    ".gitignore",
    "README.md",
    "requirements.txt",
    "render_svg.swift",
    "evaluation/test_cases.sha256",
    "analyze_results.py",
    "artifact_identity.py",
    "audit_run.py",
    "backfill_run_identity.py",
    "deploy_omlx.py",
    "evaluate.py",
    "evidence_ablation.py",
    "experiment_config.py",
    "make_assets.py",
    "package_results.py",
    "prepare_ddxplus.py",
    "qwenpaw_model.py",
    "qwenpaw_provider_state.py",
    "verify_fusion.py",
]
FORBIDDEN_KEYS = {
    "api_key",
    "access_token",
    "authorization",
    "password",
    "secret",
    "token",
    "initial_url",
    "final_url",
    "workspace_dir",
    "original_agent_selection",
    "original_global_selection",
    "restored_agent_selection",
    "original_connection_settings",
}
FORBIDDEN_TEXT = (
    "/Users/",
    "/home/",
    "-----BEGIN",
    "Bearer ",
    "file://",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads((ROOT / path).read_text())


def read_jsonl(path):
    return [
        json.loads(line)
        for line in (ROOT / path).read_text().splitlines()
        if line.strip()
    ]


def reject_sensitive(value, location="results/public"):
    if isinstance(value, dict):
        for key, item in value.items():
            require(key.lower() not in FORBIDDEN_KEYS, f"Excluded field at {location}: {key}")
            reject_sensitive(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_sensitive(item, f"{location}[{index}]")
    elif isinstance(value, str):
        require(
            not any(marker in value for marker in FORBIDDEN_TEXT),
            f"Private path or credential marker at {location}",
        )
        require("eyJ" not in value or len(value) < 100, f"Possible token at {location}")


def main():
    require(verify_test_cases() == EXPECTED_TEST_SHA256, "Unexpected held-out test set")
    audit = read_json("results/local-artifact-audit.json")
    require(audit["status"] == "passed", "Run the complete artifact and rollback audit first")
    require(audit["test_cases_sha256"] == EXPECTED_TEST_SHA256, "Audit test hash differs")
    require(audit["rollback"]["verified"] is True, "Rollback is not verified")

    PUBLIC.mkdir(parents=True, exist_ok=True)
    artifacts = {}

    def write(name, value, sources):
        reject_sensitive(value, name)
        path = PUBLIC / name
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
        artifacts[name] = {
            "sha256": file_sha256(path),
            "local_sources": sources,
            "local_source_sha256": {
                source: file_sha256(ROOT / source)
                for source in sources
            },
        }

    summaries = {}
    for output, source in SUMMARY_FILES.items():
        saved = read_json(f"results/{source}")
        summary = {
            key: saved[key]
            for key in ("mode", "cases", *METRICS, "test_cases_sha256", "generation")
        }
        require(summary["cases"] == 490, f"Incomplete evaluation: {source}")
        require(summary["test_cases_sha256"] == EXPECTED_TEST_SHA256, f"Test hash differs: {source}")
        require(summary["generation"] == GENERATION, f"Generation differs: {source}")
        require(audit["summaries"][source.removesuffix(".summary.json")] == summary, f"Audit differs: {source}")
        summaries[output] = summary
        write(output, summary, [f"results/{source}"])

    for output, source in COPY_FILES.items():
        value = read_json(f"results/{source}")
        write(output, value, [f"results/{source}"])

    review = read_json("results/fused-dequantized-full-deployment-review.json")
    require(review["status"] == "reviewed_with_differences", "Unexpected fusion review status")
    require(review["strict_identity_gate_passed"] is False, "Strict fusion identity must remain explicit")
    require(review["exact_response_matches"] == 486, "Unexpected exact-response count")
    require(review["response_difference_count"] == 4, "Unexpected fusion difference count")
    require(review["deployment_eligible"] is True, "Corrected fused artifact was not accepted")
    differences = read_json("results/fused-dequantized-full-response-differences.json")
    require(len(differences) == 4, "Not all fusion differences were selected")
    review["response_differences"] = "results/public/fused-response-differences.json"
    write(
        "fused-dequantized-deployment-review.json",
        review,
        [
            "results/fused-dequantized-full-deployment-review.json",
            "results/fused-dequantized-full-response-differences.json",
        ],
    )

    rejected = read_json("results/checkpoints/part6-quantized-verification.json")
    require(rejected["status"] == "failed", "Quantized fusion was not rejected")
    require(rejected["deployment_eligible"] is False, "Rejected fusion must not be deployable")
    require(
        summaries["fused-quantized-rejected.summary.json"]["top1_accuracy"]
        < summaries["adapter.summary.json"]["top1_accuracy"],
        "Unexpected rejected-fusion comparison",
    )

    examples = read_json("results/qualitative-examples.json")["examples"]
    require(examples["improved"]["case_id"] == "test-0001", "Improved example differs")
    require(not examples["improved"]["base"]["top1"] and examples["improved"]["adapter"]["top1"], "Invalid improved example")
    require(examples["shared_failure"]["case_id"] == "test-0000", "Shared-failure example differs")
    require(not examples["shared_failure"]["base"]["top1"] and not examples["shared_failure"]["adapter"]["top1"], "Invalid shared failure")
    require(examples["well_formatted_incorrect"]["case_id"] == "test-0002", "Formatted-failure example differs")
    require(examples["well_formatted_incorrect"]["adapter"]["structured"], "Expected a structured failure")
    require(not examples["well_formatted_incorrect"]["adapter"]["top1"], "Expected an incorrect top-1 label")

    ablation = read_json("results/counterfactual.json")
    require(ablation["case_id"] == "test-0002", "Selected ablation differs")
    require(ablation["removed_section"] == "Symptoms", "Ablation did not target Symptoms")
    require(ablation["ground_truth_after_edit"] is None, "Ablation must not assign a new label")
    require(not ablation["edited_case_has_validated_ground_truth"], "Edited case has no validated label")
    require(ablation["original_matches_adapter_evaluation"] is True, "Ablation original differs from evaluation")
    require(ablation["responses"]["original"] == ablation["responses"]["one_finding_removed"], "Reported ablation response changed")

    direct = read_json("results/omlx-verification.json")
    selected = read_json("results/omlx-selected-model.json")
    console = read_json("results/qwenpaw-console-verification.json")
    rollback = read_json("results/qwenpaw-rollback.json")
    chat_rollback = read_json("results/qwenpaw-chat-rollback.json")
    credential = read_json("results/qwenpaw-credential-sync.json")
    require(direct["model"] == selected["display_id"] == "ddxplus-qwen", "Unexpected discovered model")
    require(direct["response_model_matches_discovery"] is True, "oMLX model identity was not verified")
    require(direct["case_id"] == console["case_id"] == "test-0001", "Deployment case differs")
    require(console["selected_model"]["model"] == selected["model_id"], "QwenPaw selected a different model")
    require(console["round_trip_succeeded"] is True, "QwenPaw chat did not complete")
    require(console["matches_dataset_label"] is False, "QwenPaw qualitative result changed")
    require(console["matches_direct_omlx_response"] is False, "QwenPaw transport comparison changed")
    require(console["evaluation_metric"] is False, "QwenPaw chat is not a benchmark")
    require(console["identical_settings_benchmark"] is False, "QwenPaw settings differ by design")
    require(console["prompt_retries_for_attractive_output"] == 0, "Unexpected console prompt retries")
    require(console["prompt_sha256"] == hashlib.sha256((RESULTS / "qwenpaw-console-message.txt").read_bytes()).hexdigest(), "Console prompt hash differs")
    require(audit["deployment"]["qwenpaw_top1"] == "Acute dystonic reactions", "QwenPaw top-1 differs")
    require(rollback["configuration_backup_restored_exactly"] is True, "Global rollback was not exact")
    require(rollback["agent_backup_restored_exactly"] is True, "Agent rollback was not exact")
    require(rollback["global_selection_preserved"] is True, "Global selection was not preserved")
    require(rollback["actual_system_daemon_restarted_after_preparation"] is True, "QwenPaw daemon restart was not verified")
    require(chat_rollback["experiment_chat_override_restored"] is True, "Chat override was not restored")
    require(chat_rollback["chat_history_preserved"] is True, "Chat history was not preserved")
    require(chat_rollback["new_generation_performed"] is False, "Rollback generated an unexpected response")
    require(credential["status"] == "synchronized_permanently", "Permanent credential repair is not recorded")
    require(credential["persistent_credential_matches_current_omlx"] is True, "Credential repair was not verified")
    require(credential["credential_values_recorded"] is False, "Credential values must not be recorded")
    require(credential["restore_original_credential_during_rollback"] is False, "Stale credential must not be restored")
    write(
        "deployment-verification.json",
        {
            "model_discovery": {
                "endpoint": "/v1/models",
                "model_id": direct["model"],
                "response_model_matches_discovery": True,
            },
            "direct_omlx": direct,
            "qwenpaw": {
                "case_id": console["case_id"],
                "dataset_ground_truth_before_any_ablation": console["dataset_ground_truth"],
                "prompt_sha256": console["prompt_sha256"],
                "selected_experiment_model": direct["model"],
                "scope": "clean chat only",
                "response": console["response"],
                "parsed_top1": audit["deployment"]["qwenpaw_top1"],
                "round_trip_succeeded": True,
                "matches_dataset_label": False,
                "matches_direct_omlx_response": False,
                "evaluation_metric": False,
                "identical_settings_benchmark": False,
                "prompt_retries_for_attractive_output": 0,
                "agent_context_and_existing_generation_settings_apply": True,
            },
            "rollback": {
                "original_global_and_agent_model_selections_restored": True,
                "configuration_backups_restored_exactly": True,
                "actual_system_daemon_restarted": True,
                "experiment_chat_override_cleared": True,
                "chat_history_preserved": True,
                "new_generation_during_rollback": False,
                "permanent_credential_repair_retained": True,
                "stale_credential_restored": False,
                "adapter_and_fused_artifacts_retained": True,
                "deployed_omlx_model_retained": True,
                "optional_model_removal_performed": False,
            },
            "credential_values_included": False,
            "raw_api_payloads_and_service_state_included": False,
        },
        [
            "results/omlx-verification.json",
            "results/omlx-selected-model.json",
            "results/qwenpaw-console-verification.json",
            "results/qwenpaw-console-message.txt",
            "results/qwenpaw-rollback.json",
            "results/qwenpaw-chat-rollback.json",
            "results/qwenpaw-credential-sync.json",
        ],
    )

    environment = read_json("results/environment.json")
    require(environment["hardware"] == "tested locally on Apple Silicon", "Hardware scope differs")
    software = {
        key: environment[key]
        for key in (
            "python",
            "uv",
            "mlx",
            "mlx-lm",
            "numpy",
            "pandas",
            "transformers",
            "tokenizers",
            "safetensors",
            "huggingface-hub",
            "omlx",
            "qwenpaw",
            "hardware",
        )
    }
    helper_python = Path.home() / ".qwenpaw" / "venv" / "bin" / "python"
    helper_version = subprocess.run(
        [str(helper_python), "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    software["qwenpaw_helper_python"] = helper_version.removeprefix("Python ")
    write("software-versions.json", software, ["results/environment.json", "requirements.txt"])

    losses = read_json("results/training-losses.json")
    training = read_json("results/training-config.json")
    require(training["batch_size"] == 2, "Final training batch size changed")
    require(training["mask_prompt"] is True, "Prompt masking was not enabled")
    require(training["iters"] == 1200, "Training iterations changed")
    require(losses["training_losses"][0] == {"iteration": 10, "loss": 2.056}, "Initial training report differs")
    require(losses["training_losses"][-1] == {"iteration": 1200, "loss": 0.057}, "Final training loss differs")
    require(losses["validation_losses"][0] == {"iteration": 1, "loss": 2.257}, "Initial validation differs")
    require(losses["validation_losses"][-1] == {"iteration": 1200, "loss": 0.064}, "Final validation differs")
    runs = {}
    for prefix in ("base", "adapter", "fused", "fused-dequantized-full"):
        run = read_json(f"results/{prefix}.run.json")
        require(run["identity_capture"] == "backfilled_from_preserved_artifacts", f"Unexpected identity provenance: {prefix}")
        require(run["test_cases_sha256"] == EXPECTED_TEST_SHA256, f"Run test hash differs: {prefix}")
        expected_revision = None if run["mode"] == "fused" else MODEL_REVISION
        require(run["model_revision"] == expected_revision, f"Run model revision differs: {prefix}")
        runs[prefix] = {"identity_capture": run["identity_capture"]}

    resume_sources = {
        "base": "final-resume-base.log",
        "adapter": "final-resume-adapter.log",
        "fused-quantized-rejected": "final-resume-fused-rejected-retry.log",
        "fused-dequantized": "final-resume-fused-dequantized.log",
    }
    resume_checks = {}
    for mode, filename in resume_sources.items():
        path = RESULTS / "logs" / filename
        require("Reusing 490 verified responses" in path.read_text(), f"Resume verification failed: {mode}")
        resume_checks[mode] = {
            "verified_responses_reused": 490,
            "new_generation_performed": False,
            "log_sha256": file_sha256(path),
        }

    write(
        "run-observations.json",
        {
            "official_dataset": {
                "release": "DDXPlus Dataset English",
                "files_md5": {
                    "release_evidences.json": "0660962abe0bbf99e1fb77188c253597",
                    "release_conditions.json": "a992eadcff3099dd72e1820fbd2115aa",
                    "release_train_patients.zip": "f75a78420ccb061951daa4db2d62139b",
                    "release_validate_patients.zip": "e4db88e9082f18410de6fd0cb7e74d18",
                    "release_test_patients.zip": "6fd53d331cf19ed4439bf4f46b92ee94",
                },
                "rows": audit["dataset"]["official_rows"],
                "extensionless_zip_members_verified": True,
                "evidence_definitions": 223,
                "pathologies": 49,
            },
            "split_counts": audit["split_isolation"]["split_counts"],
            "split_prompt_overlap": 0,
            "test_prompts_and_targets_rebuilt_from_official_rows": 490,
            "test_cases": 490,
            "test_cases_sha256": EXPECTED_TEST_SHA256,
            "test_cases_with_two_reference_labels": audit["test_cases_with_two_reference_labels"],
            "generation": GENERATION,
            "base_model_revision": MODEL_REVISION,
            "evaluation_identity_provenance": runs,
            "identity_metadata_backfilled_after_generation": True,
            "identity_backfill_disclosure": "Artifact and runtime identity were reconstructed from preserved artifacts; they were not captured during original generation.",
            "no_generation_resume_checks": resume_checks,
            "training": {
                "first_reported_training_iteration": 10,
                "first_reported_training_loss": 2.056,
                "final_training_loss": 0.057,
                "initial_validation_iteration": 1,
                "initial_validation_loss": 2.257,
                "validation_loss_at_iteration_200": 0.144,
                "final_validation_loss": 0.064,
                "batch_size_one_fallback_used": False,
                "memory_pressure_configuration_change_used": False,
                "peak_memory_measured": False,
                "total_training_time_measured": False,
            },
            "smoke_tests_are_not_final_benchmarks": True,
            "fused_strict_identity_passed": False,
            "fused_reviewed_differences_accepted": True,
            "audit": {
                "status": "passed",
                "source": "results/local-artifact-audit.json",
                "sha256": file_sha256(RESULTS / "local-artifact-audit.json"),
            },
            "raw_full_responses_logs_and_private_service_state_published": False,
        },
        [
            "results/local-artifact-audit.json",
            "results/training-config.json",
            "results/training-losses.json",
            *(f"results/{prefix}.run.json" for prefix in runs),
            *(f"results/logs/{filename}" for filename in resume_sources.values()),
        ],
    )

    source_hashes = {}
    for filename in SOURCE_FILES:
        path = ROOT / filename
        require(path.is_file(), f"Missing companion source: {filename}")
        source_hashes[filename] = file_sha256(path)
    provenance = {
        "format_version": 1,
        "status": "local_review_candidate_not_yet_approved_for_commit",
        "generator": "package_results.py",
        "source_code_sha256": source_hashes,
        "artifacts": artifacts,
        "test_cases_sha256": EXPECTED_TEST_SHA256,
        "test_data_and_full_response_files_excluded": True,
        "model_weights_adapters_and_fused_models_excluded": True,
        "raw_api_payloads_credentials_account_data_and_service_state_excluded": True,
        "screenshots_and_unreviewed_raw_outputs_excluded": True,
    }
    reject_sensitive(provenance)
    (PUBLIC / "provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
    for path in PUBLIC.glob("*.json"):
        if path.name != "provenance.json":
            require(path.name in artifacts, f"Unreviewed public artifact: {path.name}")
    print(f"Wrote {len(artifacts)} curated public artifacts and provenance.json")
    print("Sensitive-field, private-path, source-hash, test-hash, metric, and rollback checks passed.")


if __name__ == "__main__":
    main()
