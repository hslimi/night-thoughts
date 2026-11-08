import argparse
import json
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from artifact_identity import artifact_fingerprint, directory_hashes, run_identity
from experiment_config import (
    EVALUATION_CASES,
    FUSED as FUSED_PATH,
    GENERATION,
    verify_test_cases,
)

ROOT = Path(__file__).resolve().parent
FUSED = ROOT / FUSED_PATH
DESTINATION = Path.home() / ".omlx" / "models" / "ddxplus-qwen"
RESULTS = ROOT / "results"
REVIEW = RESULTS / "fused-dequantized-full-deployment-review.json"


def read_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def api_request(base_url, path, api_key, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def checkpoint(stage, artifact):
    path = RESULTS / "checkpoints" / f"{stage}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "stage": stage,
                "status": "complete",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "artifact": artifact,
            },
            indent=2,
        )
        + "\n"
    )


def verify_deployment_review():
    prefix = RESULTS / "fused-dequantized-full"
    review = json.loads(REVIEW.read_text())
    run = json.loads(prefix.with_suffix(".run.json").read_text())
    summary = json.loads(prefix.with_suffix(".summary.json").read_text())
    adapter_run = json.loads((RESULTS / "adapter.run.json").read_text())
    test_sha256 = verify_test_cases()
    model_path = FUSED.relative_to(ROOT).as_posix()

    require(review["deployment_eligible"] is True, "Fused deployment review did not pass")
    require(review["model_path"] == run["model"] == model_path, "Fused model path differs")
    require(run["mode"] == summary["mode"] == "fused", "Unexpected fused evaluation mode")
    require(run["adapter"] is None, "Fused evaluation unexpectedly used an adapter")
    require(adapter_run["mode"] == "adapter", "Adapter comparison metadata is missing")
    require(
        review["cases"] == run["cases"] == summary["cases"] == EVALUATION_CASES,
        "Deployment requires all 490 held-out cases",
    )
    require(
        len(read_jsonl(prefix.with_suffix(".jsonl"))) == EVALUATION_CASES,
        "Fused response count differs from 490",
    )
    require(
        review["test_cases_sha256"]
        == run["test_cases_sha256"]
        == summary["test_cases_sha256"]
        == adapter_run["test_cases_sha256"]
        == test_sha256,
        "Evaluation test-set hashes differ",
    )
    require(
        summary["generation"] == GENERATION
        and run["max_tokens"] == GENERATION["max_tokens"]
        and run["temperature"] == GENERATION["temperature"],
        "Deployment requires the common generation settings",
    )
    for key, value in run_identity("fused", run["model"], None).items():
        require(run.get(key) == value, f"Fused artifact or runtime identity differs: {key}")
    for key, value in run_identity(
        "adapter", adapter_run["model"], adapter_run["adapter"]
    ).items():
        require(adapter_run.get(key) == value, f"Adapter comparison identity differs: {key}")
    require(
        directory_hashes(FUSED) == run["model_files_sha256"],
        "The local fused model differs from the evaluated artifact",
    )
    require(
        review["fused_artifact_sha256"]
        == artifact_fingerprint(run["model_files_sha256"]),
        "The fusion review is not bound to the evaluated fused artifact",
    )

    differences = json.loads((ROOT / review["response_differences"]).read_text())
    require(
        len(differences) == EVALUATION_CASES - review["exact_response_matches"],
        "The reviewed fusion differences are incomplete",
    )
    if not review["strict_identity_gate_passed"]:
        require(
            review["status"] == "reviewed_with_differences"
            and review["review_limits"]["review_flag_supplied"] is True,
            "Non-identical fused output requires explicit reviewed-differences acceptance",
        )
        print(
            f"Fusion review: strict identity failed; {len(differences)} "
            "response differences reviewed under the deployment criterion."
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-id", default="test-0000")
    parser.add_argument(
        "--skip-restart",
        action="store_true",
        help="Verify the running daemon after an authorized manual restart.",
    )
    args = parser.parse_args()

    verify_deployment_review()
    for required in [FUSED / "config.json", FUSED / "tokenizer.json"]:
        if not required.is_file():
            raise FileNotFoundError(required)
    if not list(FUSED.glob("*.safetensors")):
        raise FileNotFoundError("No fused-model weights found")

    source_hashes = directory_hashes(FUSED)
    if DESTINATION.exists():
        if directory_hashes(DESTINATION) != source_hashes:
            raise FileExistsError(
                "The deployment directory differs from the fused model; "
                "inspect it before replacing it."
            )
        print("Reusing the verified deployed model files")
    else:
        DESTINATION.mkdir(parents=True)
        subprocess.run(
            ["rsync", "-a", f"{FUSED}/", f"{DESTINATION}/"],
            check=True,
        )
        require(
            directory_hashes(DESTINATION) == source_hashes,
            "Deployed model checksums differ from the reviewed fused model",
        )
        print("Installed and checksum-verified the fused model files")

    settings = json.loads((Path.home() / ".omlx" / "settings.json").read_text())
    api_key = settings["auth"]["api_key"]
    if not isinstance(api_key, str) or not api_key:
        raise ValueError("oMLX API key is missing or invalid")

    if args.skip_restart:
        print("Skipping service restart; verifying the running system daemon.")
    else:
        restart = subprocess.run(
            ["sudo", "launchctl", "kickstart", "-k", "system/com.omlx.server"],
            check=True,
            capture_output=True,
            text=True,
        )
        output = (restart.stdout + restart.stderr).replace(str(Path.home()), "~")
        output = output.replace(api_key, "[REDACTED]")
        print(output, end="" if output.endswith("\n") else "\n")

    base_url = "http://localhost:8000/v1"
    last_error = None
    for _ in range(60):
        try:
            models = api_request(base_url, "/models", api_key)
            matches = sorted(
                {
                    item["id"]
                    for item in models.get("data", [])
                    if Path(item.get("id", "")).name == "ddxplus-qwen"
                }
            )
            if len(matches) > 1:
                raise ValueError("Multiple discovered ddxplus-qwen model IDs")
            if len(matches) == 1:
                break
            last_error = None
        except Exception as error:
            last_error = error
        time.sleep(2)
    else:
        raise RuntimeError(
            "oMLX did not discover exactly one ddxplus-qwen model"
        ) from last_error

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "omlx-models.json").write_text(json.dumps(models, indent=2) + "\n")
    model_id = matches[0]
    display_id = "ddxplus-qwen" if model_id != "ddxplus-qwen" else model_id
    print(f"Discovered model through /v1/models: {display_id}")

    cases = read_jsonl(ROOT / "evaluation" / "test_cases.jsonl")
    case = next((case for case in cases if case["case_id"] == args.case_id), None)
    if case is None:
        raise ValueError(f"Held-out case not found: {args.case_id}")
    metadata = json.loads((ROOT / "evaluation" / "metadata.json").read_text())
    request_body = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": metadata["system_prompt"]},
            {"role": "user", "content": case["prompt"]},
        ],
        "temperature": GENERATION["temperature"],
        "max_tokens": GENERATION["max_tokens"],
    }
    request_path = ROOT / "evaluation" / "omlx-request.json"
    request_path.write_text(json.dumps(request_body, indent=2) + "\n")
    response = api_request(base_url, "/chat/completions", api_key, request_body)
    (RESULTS / "omlx-response.json").write_text(json.dumps(response, indent=2) + "\n")

    content = response["choices"][0]["message"]["content"]
    if not isinstance(content, str) or not content.strip():
        raise ValueError("oMLX returned an empty response")
    if response.get("model") != model_id:
        raise ValueError("oMLX response model differs from the discovered model ID")

    (RESULTS / "omlx-selected-model.json").write_text(
        json.dumps({"model_id": model_id, "display_id": display_id}, indent=2) + "\n"
    )
    public = {
        "model": display_id,
        "case_id": case["case_id"],
        "source_index": case["source_index"],
        "ground_truth": case["ground_truth"],
        **GENERATION,
        "response_model_matches_discovery": True,
        "response": content,
        "test_cases_sha256": verify_test_cases(),
    }
    (RESULTS / "omlx-verification.json").write_text(
        json.dumps(public, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"Held-out case: {case['case_id']}")
    print("--- oMLX held-out response ---")
    print(content)
    checkpoint("part7-omlx", "results/omlx-verification.json")
    print("oMLX deployment and generation verified; credentials were not printed.")


if __name__ == "__main__":
    main()
