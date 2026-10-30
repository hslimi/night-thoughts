---
title: "Teaching a Small Language Model to Triage Incidents: A Beginner’s Unsloth and QLoRA Tutorial"
datePublished: 2026-10-30T00:35:01.434Z
cuid: cmvu8q2uq000102po7d656mlz
slug: teaching-a-small-language-model-to-triage-incidents-a-beginner-s-unsloth-and-qlora-tutorial
cover: https://cdn.hashnode.com/uploads/covers/6a92730f9a9aa7f72e74fdf4/6128f57e-8972-4407-8933-8ee037b84cc8.jpg
tags: ai, machine-learning, google-colab, llm, finetuning, qlora, unsloth

---

Most fine-tuning tutorials stop when the training loss decreases.

I wanted to answer a more useful operational question: can a small language model learn to turn an unstructured incident alert into a strict JSON object that another program can validate and route?

In this experiment, I used **Google Colab** for the GPU environment and **Unsloth** for QLoRA fine-tuning. I generated a synthetic incident dataset, kept entire incident scenarios out of training, compared the base and fine-tuned models on identical test cases, and saved the resulting adapter to Google Drive.

The model will not restart services, execute commands, or diagnose real infrastructure. It performs one bounded task:

```text
Unstructured alert → typed incident report → independent schema validation
```

This is an educational machine-learning experiment, not a production incident-management system.

## What We Will Build

The final pipeline looks like this:

```text
Synthetic incident scenarios
            ↓
Train / validation / test split by scenario
            ↓
Qwen2.5-1.5B-Instruct loaded in 4-bit
            ↓
Baseline evaluation on unseen test scenarios
            ↓
QLoRA training with Unsloth
            ↓
Fine-tuned evaluation on the same test cases
            ↓
LoRA adapter saved to Google Drive
```

By the end, you will know how to:

- open and configure a GPU notebook in Google Colab;
- generate a small synthetic JSONL dataset without downloading external data;
- prevent near-duplicate scenarios from leaking across dataset splits;
- format conversations with the model's own chat template;
- evaluate a base model before training;
- train a LoRA adapter with Unsloth and TRL;
- measure JSON validity, schema compliance, exact matches, and field accuracy;
- save and reload the adapter, and verify application-side schema validation.

## The Output Contract

Every alert must produce exactly six fields:

```json
{
  "service": "payments-api",
  "severity": "sev2",
  "category": "database_capacity",
  "summary": "Database connection-pool exhaustion is causing checkout timeouts",
  "next_action": "inspect_database_connections",
  "escalate": true
}
```

The allowed values are deliberately small:

| Field | Allowed values |
| --- | --- |
| `service` | `payments-api`, `authentication`, `search`, `inventory`, `notifications`, `unknown` |
| `severity` | `sev1`, `sev2`, `sev3`, `sev4` |
| `category` | `database_capacity`, `deployment_regression`, `authentication`, `network`, `unknown` |
| `next_action` | `inspect_database_connections`, `inspect_recent_deployment`, `inspect_auth_configuration`, `inspect_network_path`, `request_more_context` |
| `escalate` | JSON `true` or `false` |
| `summary` | A short, non-empty string |

When the evidence is insufficient, the target category is `unknown` and the next action is `request_more_context`. The model should not invent a root cause.

Two labels are dataset conventions rather than universal operational rules:

- `sev1` and `sev2` targets have `escalate: true`;
- `sev3` and `sev4` targets have `escalate: false`.

A real organization would define these mappings through its own incident policy.

## Prerequisites

You need:

- a Google account;
- access to [Google Colab](https://colab.research.google.com/);
- enough free Google Drive space for the dataset and adapter;
- a modern browser.

You do **not** need:

- a local GPU;
- a Hugging Face account for the core tutorial;
- a pre-existing dataset;
- previous experience with Unsloth;
- any real production logs.

GPU availability and runtime limits depend on Colab availability, account limits, and plan. Do not start with the optional merged-model export until the core experiment works.

## Part 1: Create the Colab Notebook

1. Open [Google Colab](https://colab.research.google.com/).
2. Select **New Notebook**.
3. Rename it to `incident-triage-unsloth.ipynb`.
4. Open **Runtime → Change runtime type**.
5. Select an available **GPU** accelerator.
6. Save the setting.

The exact GPU offered may vary. This tutorial uses a small 1.5B-parameter model and short examples to keep the experiment accessible.

### Cell 1 — Verify the GPU

Run:

```python
import torch

print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

assert torch.cuda.is_available(), (
    "No GPU is active. Open Runtime → Change runtime type and select GPU."
)

print("GPU:", torch.cuda.get_device_name(0))
print("VRAM (GB):", round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1))
```

**Expected result:** `CUDA available: True`, followed by the GPU name. If the assertion fails, change the runtime type before continuing.

The actual runtime reported PyTorch 2.11.0+cu130, CUDA availability, and an NVIDIA RTX PRO 6000 Blackwell Server Edition with approximately 102 GB VRAM.

![Colab GPU verification showing the RTX PRO 6000 and 102 GB VRAM](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/c2398306-0f78-40cf-bad9-2acb5a78f7e6.png align="center")

## Part 2: Create a Persistent Project Folder

Colab runtimes are temporary. Files stored only under `/content` can disappear when the runtime resets. We will keep generated data, predictions, metrics, and the final adapter in Google Drive.

### Cell 2 — Mount Google Drive

```python
from google.colab import drive
from pathlib import Path

drive.mount("/content/drive")

PROJECT_DIR = Path("/content/drive/MyDrive/nightthoughts-incident-triage")
DATA_DIR = PROJECT_DIR / "data"
RESULTS_DIR = PROJECT_DIR / "results"
ADAPTER_DIR = PROJECT_DIR / "adapter"

for directory in [PROJECT_DIR, DATA_DIR, RESULTS_DIR, ADAPTER_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

print("Project folder:", PROJECT_DIR)
```

Colab will ask you to authorize Drive access. Select the same Google account you want to use for the experiment.

![Google Drive mounted and the incident-triage project folder created](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/798afdd6-cd16-415d-86f0-d58d24a6fe7f.png align="center")

## Part 3: Install Unsloth

### Cell 3 — Install the packages

```python
!pip install -q unsloth
```

This can take a few minutes. If Colab reports dependency conflicts or an import fails immediately afterward, use **Runtime → Restart session**, then run the Drive-mount cell again before continuing. You do not normally need to reinstall after every ordinary cell.

### Cell 4 — Import Unsloth

```python
from unsloth import FastLanguageModel

print("Unsloth imported successfully.")
```

Unsloth imported successfully. It warned that the installed xformers build did not match PyTorch 2.11.0+cu130 and used PyTorch attention instead. I kept that documented fallback rather than changing the tutorial environment.

![Cell used to install Unsloth](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/37cdf04e-bcec-4057-8019-c4bf760565ce.png align="center")

## Part 4: Generate the Synthetic Dataset

An available public log dataset would not necessarily contain our target labels, summaries, severity policy, and investigation actions. Instead, we will generate examples from **25 manually defined incident scenarios**:

- 15 training scenarios;
- 5 validation scenarios;
- 5 test scenarios.

Each split contains all five categories. A scenario assigned to test never appears in training or validation.

This is not a large or realistic production corpus. It is a controlled experiment for testing whether a small model can learn a constrained transformation and generalize to unseen incident descriptions.

### Cell 5 — Define the scenarios and output vocabulary

This is the longest cell in the tutorial. Paste it as one block.

```python
import json
import random
from collections import Counter, defaultdict

SCENARIOS = [
    # Training scenarios
    dict(id="db_pool_payments", split="train", service="payments-api", severity="sev2", category="database_capacity", next_action="inspect_database_connections", summary="Database connection-pool exhaustion is causing checkout timeouts", alert="Payments API checkout timeouts reached {pct}% after the database connection pool hit its limit. Retries are increasing and {n}% of requests are queued."),
    dict(id="db_connections_inventory", split="train", service="inventory", severity="sev2", category="database_capacity", next_action="inspect_database_connections", summary="Inventory workers cannot obtain enough database connections", alert="Inventory workers have exhausted their PostgreSQL connections. Stock updates are waiting for a free connection and the backlog has reached {n} jobs."),
    dict(id="db_slow_queries_search", split="train", service="search", severity="sev3", category="database_capacity", next_action="inspect_database_connections", summary="Search latency is rising under expensive database queries", alert="Search p95 latency increased to {n} ms. The primary database shows concurrent expensive queries and CPU saturation, but the last deployment was three days ago."),
    dict(id="deploy_checkout_timeouts", split="train", service="payments-api", severity="sev1", category="deployment_regression", next_action="inspect_recent_deployment", summary="Checkout failures began immediately after a payments deployment", alert="At 02:{minutes}, version 2026.10.{n} was deployed to payments-api. Within two minutes, checkout errors rose to {pct}% while the previous version remains healthy."),
    dict(id="deploy_search_errors", split="train", service="search", severity="sev2", category="deployment_regression", next_action="inspect_recent_deployment", summary="Search errors started with the latest release", alert="The search service began returning 500 responses immediately after release {n}. Error rate is {pct}%; the canary did not show this behavior."),
    dict(id="deploy_auth_config", split="train", service="authentication", severity="sev2", category="deployment_regression", next_action="inspect_recent_deployment", summary="Login failures followed an authentication configuration release", alert="A configuration deployment to authentication completed {minutes} minutes ago. Since then, valid logins have failed across all regions; authentication CPU and network metrics are normal."),
    dict(id="auth_token_clock", split="train", service="authentication", severity="sev3", category="authentication", next_action="inspect_auth_configuration", summary="Token validation is failing because of clock or timestamp checks", alert="Authentication rejects otherwise valid JWTs with not-before and expiration errors. One node reports a clock offset of {n} seconds; traffic and recent deployments are unchanged."),
    dict(id="auth_sso_loop", split="train", service="authentication", severity="sev2", category="authentication", next_action="inspect_auth_configuration", summary="Users are trapped in an SSO redirect loop", alert="Users cannot complete SSO login and loop between the identity provider and authentication. The callback reports a state or nonce mismatch for {pct}% of attempts."),
    dict(id="auth_permission_cache", split="train", service="authentication", severity="sev3", category="authentication", next_action="inspect_auth_configuration", summary="Authorization changes are not taking effect", alert="Revoked user permissions remain valid for up to {minutes} minutes. Authentication logs show stale role claims served from the authorization cache."),
    dict(id="network_dns_inventory", split="train", service="inventory", severity="sev2", category="network", next_action="inspect_network_path", summary="Inventory dependencies are unreachable because DNS resolution fails", alert="Inventory cannot resolve its database hostname. DNS lookups time out in two availability zones, while direct connections to the previously resolved address still work."),
    dict(id="network_packet_loss_payments", split="train", service="payments-api", severity="sev1", category="network", next_action="inspect_network_path", summary="Packet loss is disrupting payments traffic", alert="Payments-api is timing out across multiple backends. The network path shows {pct}% packet loss and retransmissions; application error logs have not changed."),
    dict(id="network_lb_search", split="train", service="search", severity="sev2", category="network", next_action="inspect_network_path", summary="One load-balancer route is dropping search requests", alert="Search requests fail only through one load-balancer route. Backend health checks pass locally, but the affected route resets {pct}% of connections."),
    dict(id="unknown_queue_notifications", split="train", service="unknown", severity="sev3", category="unknown", next_action="request_more_context", summary="The alert does not isolate a cause for delayed asynchronous work", alert="Asynchronous work is delayed and a queue depth graph is rising. Dashboards disagree about the owning service, and no dependency, release, or error evidence is available."),
    dict(id="unknown_disk_inventory", split="train", service="unknown", severity="sev3", category="unknown", next_action="request_more_context", summary="A host disk warning lacks enough evidence for incident classification", alert="A host is above {pct}% disk usage. The owning application and customer impact are unclear, and there is no evidence yet of database, deployment, authentication, or network failure."),
    dict(id="unknown_third_party", split="train", service="unknown", severity="sev4", category="unknown", next_action="request_more_context", summary="A vendor notice has no established service impact", alert="A third-party provider reports degradation in one region. Our monitoring shows no confirmed impact, affected service, or relevant internal errors."),

    # Validation scenarios: none appear in training
    dict(id="db_replication_lag", split="validation", service="inventory", severity="sev2", category="database_capacity", next_action="inspect_database_connections", summary="Database replication lag is overloading the inventory primary", alert="Inventory reads are being redirected to the primary because replica lag exceeds {n} seconds. Primary connections and query latency are now climbing."),
    dict(id="deploy_notification_retry", split="validation", service="notifications", severity="sev3", category="deployment_regression", next_action="inspect_recent_deployment", summary="A notification release introduced excessive retries", alert="Notification retry volume tripled immediately after worker release {n}. Delivery latency is increasing, while the previous worker version processes the same events normally."),
    dict(id="auth_expired_certificate", split="validation", service="authentication", severity="sev1", category="authentication", next_action="inspect_auth_configuration", summary="An expired signing certificate is blocking authentication", alert="All new SSO assertions fail signature validation. The authentication signing certificate expired {minutes} minutes ago; infrastructure connectivity is healthy."),
    dict(id="network_gateway_timeouts", split="validation", service="notifications", severity="sev2", category="network", next_action="inspect_network_path", summary="Gateway timeouts are interrupting notification delivery", alert="Notifications cannot reach the external gateway. TCP connections time out after {n} seconds in every region, while internal service-to-service calls remain healthy."),
    dict(id="unknown_metrics_gap", split="validation", service="unknown", severity="sev4", category="unknown", next_action="request_more_context", summary="Missing telemetry prevents a supported classification", alert="A dashboard panel has been blank for {minutes} minutes. The affected service, user impact, and underlying error are unknown."),

    # Test scenarios: unseen during both training and model selection
    dict(id="db_deadlock_payments", split="test", service="payments-api", severity="sev2", category="database_capacity", next_action="inspect_database_connections", summary="Database deadlocks are reducing payments capacity", alert="Payments-api database deadlocks increased to {n} per minute. Transactions roll back and connection wait time is rising, although no release occurred today."),
    dict(id="deploy_migration_errors", split="test", service="payments-api", severity="sev1", category="deployment_regression", next_action="inspect_recent_deployment", summary="A schema migration release broke payment writes", alert="Payment writes fail with an unknown-column error immediately after migration release {n}. Reads on the old path are healthy and failures correlate exactly with rollout progress."),
    dict(id="auth_key_rotation", split="test", service="authentication", severity="sev2", category="authentication", next_action="inspect_auth_configuration", summary="A signing-key rotation broke token verification", alert="Token verification began failing after last night's signing-key rotation. Old and new keys are being served inconsistently across authentication nodes."),
    dict(id="network_ipv6_route", split="test", service="search", severity="sev3", category="network", next_action="inspect_network_path", summary="A broken IPv6 route is delaying search dependencies", alert="Search dependency calls over IPv6 time out, forcing connection fallback after {n} seconds. IPv4 requests to the same hosts complete normally."),
    dict(id="unknown_worker_saturation", split="test", service="unknown", severity="sev3", category="unknown", next_action="request_more_context", summary="Generic worker saturation has no isolated root cause", alert="Several workers report high CPU and slower processing. There is no confirmed owning service, recent release, dependency failure, or authentication evidence."),
]

SERVICES = ["payments-api", "authentication", "search", "inventory", "notifications", "unknown"]
SEVERITIES = ["sev1", "sev2", "sev3", "sev4"]
CATEGORIES = ["database_capacity", "deployment_regression", "authentication", "network", "unknown"]
ACTIONS = [
    "inspect_database_connections",
    "inspect_recent_deployment",
    "inspect_auth_configuration",
    "inspect_network_path",
    "request_more_context",
]

print("Scenarios by split:", Counter(s["split"] for s in SCENARIOS))
```

### Cell 6 — Generate the examples

Each example receives random metric values and optional context. An incident reference makes every alert unique without encoding its label.

```python
PREFIXES = ["", "[alertmanager] ", "PRODUCTION: ", "On-call note: ", "Incident update: "]
SUFFIXES = [
    "",
    " The runbook has not been updated.",
    " No remediation has been attempted.",
    " Customer support is monitoring the situation.",
    " Keep this as an investigation-only alert.",
]

TARGET_FIELDS = ["service", "severity", "category", "summary", "next_action", "escalate"]

def make_record(scenario, sequence, rng):
    values = {
        "n": rng.randint(4, 900),
        "pct": rng.randint(8, 65),
        "minutes": rng.randint(2, 55),
    }

    alert = scenario["alert"].format(**values)
    alert = rng.choice(PREFIXES) + alert + rng.choice(SUFFIXES)
    alert += f" Incident reference: INC-{sequence:05d}."

    target = {key: scenario[key] for key in TARGET_FIELDS[:-1]}
    target["escalate"] = scenario["severity"] in {"sev1", "sev2"}

    return {
        "scenario_id": scenario["id"],
        "split": scenario["split"],
        "alert": alert,
        "target": json.dumps(target, ensure_ascii=False),
    }

rng = random.Random(3407)
records = []
examples_per_split = {"train": 100, "validation": 80, "test": 80}

sequence = 0
for scenario in SCENARIOS:
    for _ in range(examples_per_split[scenario["split"]]):
        sequence += 1
        records.append(make_record(scenario, sequence, rng))

train_records = [r for r in records if r["split"] == "train"]
validation_records = [r for r in records if r["split"] == "validation"]
test_records = [r for r in records if r["split"] == "test"]

print("Examples:", {split: len(items) for split, items in {
    "train": train_records,
    "validation": validation_records,
    "test": test_records,
}.items()})
print("Unique alerts:", len({r["alert"] for r in records}))
print("First target:", test_records[0]["target"])
```

**Expected counts:** 1,500 training examples, 400 validation examples, and 400 test examples. All 2,300 alerts should be unique.

The actual counts matched those requirements exactly.

![Actual dataset counts showing 1500 training, 400 validation, 400 test, and 2300 unique alerts](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/8171b0c9-45ac-49f7-89e9-da19c8ce106d.png align="center")

### Cell 7 — Verify the split boundaries

Do not skip this cell. A split check is part of the experiment, not ceremonial bookkeeping.

```python
scenario_sets = {
    split: {r["scenario_id"] for r in items}
    for split, items in {
        "train": train_records,
        "validation": validation_records,
        "test": test_records,
    }.items()
}

assert not scenario_sets["train"] & scenario_sets["validation"]
assert not scenario_sets["train"] & scenario_sets["test"]
assert not scenario_sets["validation"] & scenario_sets["test"]
assert len({r["alert"] for r in records}) == len(records)

for split, items in {
    "train": train_records,
    "validation": validation_records,
    "test": test_records,
}.items():
    category_counts = Counter(json.loads(r["target"])["category"] for r in items)
    print(split, "scenario IDs:", sorted(scenario_sets[split]))
    print(split, "categories:", dict(category_counts))
```

**Expected result:** no assertion error, and every split contains all five categories.

The assertions passed. The run produced 15 training scenario IDs, five validation IDs, and five test IDs, with no overlap and all five categories in every split.

![Scenario IDs and category counts verifying disjoint dataset splits](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/0b4bbf4b-638e-4b71-a4ef-b78cd88697ff.png align="center")

### Cell 8 — Inspect and save the JSONL files

```python
for record in test_records[:2]:
    print("ALERT:", record["alert"])
    print("TARGET:", record["target"])
    print()

for split, items in {
    "train": train_records,
    "validation": validation_records,
    "test": test_records,
}.items():
    path = DATA_DIR / f"{split}.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for record in items:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print("Saved", len(items), "examples to", path)
```

Read a sample manually. Synthetic data can still contain bad labels, contradictory wording, and unrealistic assumptions. For a larger experiment, inspect a random sample from every scenario before training.

## Part 5: Format the Conversations

The model receives a system prompt, an alert, and—only in training and validation—the target JSON object. Test targets remain stored for scoring but are not included in test prompts.

### Cell 9 — Define the system prompt and message structure

```python
SYSTEM_PROMPT = f"""You convert incident alerts into strict JSON objects.
Return one JSON object and nothing else. Do not use Markdown fences.
Use exactly these keys: service, severity, category, summary, next_action, escalate.
Allowed service values: {json.dumps(SERVICES)}.
Allowed severity values: {json.dumps(SEVERITIES)}.
Allowed category values: {json.dumps(CATEGORIES)}.
Allowed next_action values: {json.dumps(ACTIONS)}.
summary must be a short non-empty string. escalate must be a JSON boolean.
Escalate sev1 and sev2. Do not escalate sev3 and sev4.
If the evidence is insufficient, use category unknown, service unknown,
and next_action request_more_context rather than inventing a cause."""

def prompt_messages(alert):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Classify this incident alert.\n\n" + alert},
    ]

def training_messages(record):
    target = json.dumps(json.loads(record["target"]), ensure_ascii=False, separators=(",", ":"))
    return prompt_messages(record["alert"]) + [
        {"role": "assistant", "content": target}
    ]

print(SYSTEM_PROMPT)
print(training_messages(train_records[0]))
```

## Part 6: Load the Base Model

We will use `unsloth/Qwen2.5-1.5B-Instruct`. It is small enough for an introductory experiment while still supporting conversational instruction following.

`load_in_4bit=True` loads the base weights in 4-bit precision. It does not mean the entire training procedure becomes four times faster or that every model will fit every GPU.

### Cell 10 — Load the model and tokenizer

```python
MAX_SEQ_LENGTH = 1024
BASE_MODEL = "unsloth/Qwen2.5-1.5B-Instruct"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=True,
)

print("Loaded:", BASE_MODEL)
print("Tokenizer chat template available:", tokenizer.chat_template is not None)
```

The first run downloads the model. Later runs may reuse cached files.

The base model loaded in 4-bit and the tokenizer reported an available chat template.

![Qwen2.5-1.5B-Instruct loaded in 4-bit with a chat template](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/48be144e-21d6-464f-891b-d95f5d39efda.png align="center")

### Cell 11 — Render the training text with the chat template

```python
from datasets import Dataset

def to_training_text(record):
    return tokenizer.apply_chat_template(
        training_messages(record),
        tokenize=False,
        add_generation_prompt=False,
    )

train_dataset = Dataset.from_list([
    {"text": to_training_text(record)} for record in train_records
])

validation_dataset = Dataset.from_list([
    {"text": to_training_text(record)} for record in validation_records
])

print(train_dataset)
print(train_dataset[0]["text"])
```

The printed text should contain the system prompt, user alert, assistant JSON response, and the special tokens required by Qwen's chat template. Do not manually add a second copy of those tokens.

![A training conversation rendered with Qwen's chat template](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/51db2e20-f514-4726-bc5f-1b0ff22cafaa.png align="center")

## Part 7: Build the Evaluator

We will evaluate behavior, not just loss.

The evaluator distinguishes:

- **JSON-valid:** the complete output parses as one JSON object;
- **schema-valid:** it also has exactly the required keys, types, and allowed values;
- **exact match:** every field equals the target;
- **field accuracy:** a field equals its target, with invalid outputs counted as failures;
- **unknown-category recall:** ambiguous cases correctly retain `category: unknown`.

Markdown fences, explanations before the object, or trailing commentary fail the strict JSON check. That is intentional: the output is an application interface.

### Cell 12 — Define generation and strict validation

```python
import pandas as pd


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
```

## Part 8: Evaluate the Base Model

Evaluating all 400 test cases before and after training would be more thorough but slower. For this introductory run, use eight cases from each of the five test scenarios: **40 identical held-out cases** for both evaluations.

### Cell 13 — Select the fixed evaluation subset

```python
EVAL_PER_SCENARIO = 8
by_scenario = defaultdict(list)

for record in test_records:
    by_scenario[record["scenario_id"]].append(record)

eval_records = []
for scenario_id in sorted(by_scenario):
    eval_records.extend(by_scenario[scenario_id][:EVAL_PER_SCENARIO])

assert len(eval_records) == 40
print("Evaluation scenarios:", sorted(by_scenario))
print("Evaluation cases:", len(eval_records))
```

For a stronger final experiment, increase `EVAL_PER_SCENARIO` to `80` and rerun both evaluations. Do not change the subset between the base and fine-tuned runs.

### Cell 14 — Run the baseline

```python
FastLanguageModel.for_inference(model)

sample = eval_records[0]
print("ALERT:\n", sample["alert"])
print("\nBASE OUTPUT:\n", generate_answer(sample["alert"]))
print("\nTARGET:\n", sample["target"])
```

If the output is truncated, increase `max_new_tokens` in `generate_answer` from 180 to 256. Keep it unchanged for all subsequent evaluations.

The actual base sample was not truncated, so I kept 180 tokens. It wrapped the object in Markdown fences and also predicted several incorrect fields. Strict scoring rejects those fences.

![Base model sample with Markdown fences and an incorrect incident classification](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/b77766a0-8e1d-4118-a9c7-75be077d8862.png align="center")

Now run the full 40-case baseline:

```python
base_predictions = evaluate_model(eval_records, mode="base")
base_metrics = summarize_predictions(base_predictions)

with (RESULTS_DIR / "base_predictions.json").open("w", encoding="utf-8") as handle:
    json.dump(base_predictions, handle, ensure_ascii=False, indent=2)

with (RESULTS_DIR / "base_metrics.json").open("w", encoding="utf-8") as handle:
    json.dump(base_metrics, handle, indent=2)

pd.Series(base_metrics)
```

Save these numbers. They are the comparison point for the adapter.

The saved baseline contained 40 prediction rows. All strict metrics were 0.00%; this is not a fence-stripped semantic score.

![Saved baseline metrics showing zero percent under the strict evaluator](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/f7a06341-690b-455b-8abb-329d544987c5.png align="center")

## Part 9: Add QLoRA Adapters

QLoRA keeps the quantized base model frozen and trains a small set of low-rank adapter parameters. This is much more accessible than updating every model weight.

For this run, the important details are:

- the base model is loaded in 4-bit precision;
- most base weights remain frozen;
- LoRA introduces trainable low-rank adapter matrices;
- only adapter parameters are updated;
- `r=16` is the adapter rank, meaning the inner dimension of those low-rank matrices;
- gradient accumulation combines micro-batches and therefore changes the effective batch size;
- QLoRA reduces memory requirements, but it does not guarantee better accuracy.

### Cell 15 — Attach the adapters

```python
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=3407,
)

print("LoRA adapters attached.")
```

`r=16` controls the adapter rank. It is a reasonable starting setting, not a universally optimal value.

![QLoRA configuration showing rank 16 and the target modules](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/d73b999f-ca50-4fcf-9a79-96be31e3f159.png align="center")

## Part 10: Train the Adapter

We will run 200 optimizer steps with an effective batch size of 8:

- per-device batch size: 2;
- gradient accumulation: 4;
- effective batch: 2 × 4 = 8.

Validation loss runs every 50 steps. Behavioral evaluation still happens separately afterward; a lower validation loss does not prove valid JSON or correct incident labels.

### Cell 16 — Configure and run training

```python
from trl import SFTConfig, SFTTrainer

FastLanguageModel.for_training(model)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    eval_dataset=validation_dataset,
    args=SFTConfig(
        output_dir="/content/incident_triage_checkpoints",
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=4,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        max_steps=200,
        learning_rate=2e-4,
        logging_steps=5,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="no",
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        dataset_num_proc=1,
        report_to="none",
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
    ),
)

trainer_stats = trainer.train()
print(trainer_stats)
```

The run completed all 200 optimizer steps. The training cell took 111.204 seconds; the trainer reported `train_runtime: 107.3805` seconds.

![Training output at step 200 with real validation losses](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/bf864781-b11e-49ab-b819-0c6e8a45fa77.png align="center")

### What the actual loss curves show

Training loss fell from **3.045980 at step 5** to **0.051658 at step 200**. It decreased sharply through step 50 and then mostly plateaued around 0.05–0.07, with small fluctuations.

Validation loss did **not** follow the same direction. It increased at every measured checkpoint: **0.631923 at step 50**, **0.756127 at step 100**, **0.808638 at step 150**, and **0.838244 at step 200**. This is a clear train/validation divergence in this run and is consistent with worsening generalization, although four validation points from one run are not enough for a universal overfitting diagnosis. Additional steps are not justified by this run alone.

Training and validation losses may be logged at different steps. The diagram uses only entries from `trainer.state.log_history`; it does not smooth the training curve or invent intermediate validation points. A loss curve alone cannot prove valid JSON or correct incident classification.

![Training loss decreasing and plateauing while validation loss rises from step 50 to 200](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/69d74518-8e84-4219-8d70-157853778d96.png align="center")

If you only want a quick pipeline test, change `max_steps` to `20`. Treat that as a smoke test, not the final experiment.

If training stops with a CUDA out-of-memory error, restart the session, rerun from the Drive setup, and change:

```python
per_device_train_batch_size = 1
```

Keep `gradient_accumulation_steps=4`; the effective batch size then becomes 4.

## Part 11: Evaluate the Fine-Tuned Model

### Cell 17 — Generate a sample

```python
FastLanguageModel.for_inference(model)

print("ALERT:\n", sample["alert"])
print("\nFINE-TUNED OUTPUT:\n", generate_answer(sample["alert"]))
print("\nTARGET:\n", sample["target"])
```

![Fine-tuned sample producing valid JSON but incorrect incident fields](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/0b08827b-0220-48dd-9c97-ecd130a61903.png align="center")

### Cell 18 — Evaluate the same 40 cases

```python
finetuned_predictions = evaluate_model(eval_records, mode="finetuned")
finetuned_metrics = summarize_predictions(finetuned_predictions)

with (RESULTS_DIR / "finetuned_predictions.json").open("w", encoding="utf-8") as handle:
    json.dump(finetuned_predictions, handle, ensure_ascii=False, indent=2)

with (RESULTS_DIR / "finetuned_metrics.json").open("w", encoding="utf-8") as handle:
    json.dump(finetuned_metrics, handle, indent=2)

comparison = pd.DataFrame({
    "base": pd.Series(base_metrics),
    "finetuned": pd.Series(finetuned_metrics),
})
comparison["difference"] = comparison["finetuned"] - comparison["base"]
comparison
```

Rates are stored between 0 and 1. For example, `0.925` means 92.5%. The `difference` column is an absolute change in rate, not a relative percentage improvement.

### Cell 19 — Show the comparison as percentages

```python
rate_metrics = [name for name in base_metrics if name != "cases"]
percentages = comparison.loc[rate_metrics, ["base", "finetuned", "difference"]] * 100
percentages.round(2)
```

![Base and fine-tuned metrics with absolute percentage-point changes](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/e7bc6b95-b04e-4718-ad8d-def442dc790e.png align="center")

Do not assume every metric must improve. A model can produce perfectly valid JSON while learning the wrong category. Exact matches and per-field behavior matter.

## Part 12: Inspect Failures

Aggregate scores hide useful information. Print examples where the fine-tuned output was invalid or did not exactly match the target.

### Cell 20 — Inspect incorrect cases

```python
failures = [p for p in finetuned_predictions if not p["exact_match"]]
print("Fine-tuned failures:", len(failures), "of", len(finetuned_predictions))

for failure in failures[:5]:
    print("\nSCENARIO:", failure["scenario_id"])
    print("ALERT:", failure["alert"])
    print("MODEL OUTPUT:", failure["raw_output"])
    print("TARGET:", json.dumps(failure["target"], ensure_ascii=False))
    print("JSON valid:", failure["json_valid"], "Schema valid:", failure["schema_valid"])
```

For each failure, ask:

1. Was the alert genuinely ambiguous?
2. Did the model choose a plausible but different service or category?
3. Did it ignore the severity policy?
4. Did it produce extra prose or an invalid type?
5. Did it invent a specific cause for an `unknown` example?
6. Is the target itself wrong or unrealistic?

Keep both successes and failures in the article. A small synthetic experiment is more credible when its limitations are visible.

![Failure inspection showing 40 non-exact fine-tuned cases and concrete misclassifications](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/83a6303a-9956-4596-83d8-4bd46b16dc40.png align="center")

## Part 13: Save and Reload the Adapter

The adapter requires the original base model. It is not a standalone full model.

### Cell 21 — Save the adapter and tokenizer

```python
model.save_pretrained(str(ADAPTER_DIR))
tokenizer.save_pretrained(str(ADAPTER_DIR))

print("Adapter saved to:", ADAPTER_DIR)
print("Files:", sorted(path.name for path in ADAPTER_DIR.iterdir()))
```

The saved directory should include adapter configuration and weight files, plus tokenizer files. Because it is on Drive, it should remain after the Colab runtime ends.

![Adapter and tokenizer files saved to Google Drive](https://cdn.hashnode.com/uploads/gql/6a92730f9a9aa7f72e74fdf4/bb7fbfef-b732-4581-a057-06ea6e16be04.png align="center")

The adapter also reloaded successfully from Drive. No merged-model export or Apple Silicon/MLX conversion was needed for this core experiment.

### Reloading in a fresh session

After a runtime restart, mount Drive again, define `ADAPTER_DIR`, and run:

```python
from unsloth import FastLanguageModel

ADAPTER_DIR = "/content/drive/MyDrive/nightthoughts-incident-triage/adapter"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=ADAPTER_DIR,
    max_seq_length=1024,
    dtype=None,
    load_in_4bit=True,
)

FastLanguageModel.for_inference(model)
print("Adapter reloaded.")
```

To generate after reloading, you must also redefine `SERVICES`, `SEVERITIES`, `CATEGORIES`, `ACTIONS`, `SYSTEM_PROMPT`, `prompt_messages`, and `generate_answer` from the earlier cells. This is why saving the notebook alongside the adapter matters.

## Part 14: Add Independent Application-Side Validation

A fine-tuned model is not a schema validator. The application must still validate every result before using it.

A minimal routing pattern is:

```python
def route_incident(alert):
    raw_output = generate_answer(alert)
    parsed, json_valid, schema_valid = validate_prediction(raw_output)

    if not schema_valid:
        return {
            "status": "manual_review",
            "reason": "The model output did not satisfy the incident schema.",
            "raw_output": raw_output,
        }

    if parsed["category"] == "unknown":
        return {
            "status": "request_more_context",
            "report": parsed,
        }

    return {
        "status": "validated_for_human_review",
        "report": parsed,
    }
```

Notice what this function does **not** do: it does not execute `next_action`, restart a service, roll back a deployment, or modify infrastructure. Those decisions belong behind separate authorization and safety controls.

## Actual Results

All values below come from the saved prediction, metric, metadata, and trainer-log files. The complete notebook, datasets, predictions, plotting source, and screenshots are in the [GitHub experiment folder](https://github.com/hslimi/night-thoughts/tree/main/experiments/incident-triage-unsloth).

### Experimental setup

- Base model: `unsloth/Qwen2.5-1.5B-Instruct`, loaded in 4-bit
- Training examples: **1,500**
- Validation examples: **400**
- Total test examples generated: **400**
- Unique alerts: **2,300**
- Fixed behavioral evaluation subset: **40**, eight per unseen test scenario
- Training steps: **200**
- LoRA rank: **16**
- Maximum sequence length: **1,024**
- GPU used: **NVIDIA RTX PRO 6000 Blackwell Server Edition**, approximately **102 GB VRAM**

### Base versus fine-tuned results

Rates are shown as percentages. The change column is an absolute change in **percentage points (pp)**, not a relative improvement.

| Metric | Base | Fine-tuned | Absolute change |
| --- | --: | --: | --: |
| JSON validity | 0.00% | 100.00% | +100.00 pp |
| Schema validity | 0.00% | 100.00% | +100.00 pp |
| Exact match | 0.00% | 0.00% | +0.00 pp |
| Service accuracy | 0.00% | 97.50% | +97.50 pp |
| Severity accuracy | 0.00% | 42.50% | +42.50 pp |
| Category accuracy | 0.00% | 60.00% | +60.00 pp |
| Summary accuracy | 0.00% | 0.00% | +0.00 pp |
| Next-action accuracy | 0.00% | 70.00% | +70.00 pp |
| Escalation accuracy | 0.00% | 60.00% | +60.00 pp |
| Unknown-category recall | 0.00% | 100.00% | +100.00 pp |

### How to interpret the behavior

The adapter clearly learned the output interface: strict JSON and schema validity both improved by 100 percentage points. That is a real improvement, but it is not the same as solving incident triage.

Exact match remained **0.00%**, and summary accuracy also remained **0.00%**. Service recognition was strong at **97.50%**, while severity accuracy was only **42.50%**. Category, next-action, and escalation accuracy reached **60.00%**, **70.00%**, and **60.00%** respectively. Both `auth_key_rotation` and `deploy_migration_errors` received the correct category for 0 of 8 cases; the other three test scenarios received 8 of 8.

Unknown-category recall reached **100.00%**, but that represents only eight synthetic ambiguous alerts. It does not establish reliable abstention on real incidents.

The zero baseline field scores also need context. The base model often emitted readable objects inside Markdown fences. The strict evaluator rejects the entire output, and invalid outputs count as failures for field accuracy. These results therefore measure the complete application contract, not a separate fence-stripped semantic evaluation.

### One partially successful held-out case—not an exact match

No case matched all six fields exactly. This example from `unknown_worker_saturation` matched **five of six fields**: service, severity, category, next action, and escalation. Only the summary differed.

**Alert:**

```text
Several workers report high CPU and slower processing. There is no confirmed owning service, recent release, dependency failure, or authentication evidence. Customer support is monitoring the situation. Incident reference: INC-02222.
```

**Fine-tuned output:**

```json
{"service":"unknown","severity":"sev3","category":"unknown","summary":"Worker complaints without clear incident evidence","next_action":"request_more_context","escalate":false}
```

**Target:**

```json
{"service":"unknown","severity":"sev3","category":"unknown","summary":"Generic worker saturation has no isolated root cause","next_action":"request_more_context","escalate":false}
```

This is a useful partial success because the model preserved uncertainty and requested more context. It still does not count as an exact match.

### One genuine failure

**Alert:**

```text
Token verification began failing after last night's signing-key rotation. Old and new keys are being served inconsistently across authentication nodes. Customer support is monitoring the situation. Incident reference: INC-02061.
```

**Fine-tuned output:**

```json
{"service":"authentication","severity":"sev3","category":"deployment_regression","summary":"Token validations are failing because different parts of the network use distinct key rings","next_action":"inspect_auth_configuration","escalate":false}
```

**Target:**

```json
{"service":"authentication","severity":"sev2","category":"authentication","summary":"A signing-key rotation broke token verification","next_action":"inspect_auth_configuration","escalate":true}
```

**What happened:** the output was valid JSON and schema-valid, but the model predicted `sev3` instead of `sev2`, `deployment_regression` instead of `authentication`, and `escalate: false` instead of `true`. It also generated a different summary. This example shows why schema validation cannot replace task evaluation or human review.

### What this 40-case subset can and cannot establish

The paired subset is enough to demonstrate a substantial change in output formatting and to expose remaining field-level failures in this particular run. It is too small for strong performance claims. The alerts are synthetic and template-derived, and agreement with tutorial labels is not proof of real-world incident-diagnosis accuracy. A stronger follow-up would evaluate all 400 test cases and add independently written, human-reviewed scenarios.

## Troubleshooting

### `CUDA available: False`

No GPU is attached. Open **Runtime → Change runtime type**, select GPU, and rerun the notebook. If no GPU is available, wait or use another available runtime rather than attempting QLoRA on CPU.

### `No module named 'unsloth'` after installation

Restart the session once, mount Drive again, and retry the import. Then continue from the dataset cells.

### CUDA out of memory during training

Change the per-device training batch size to 1. If necessary, reduce `MAX_SEQ_LENGTH` to 768 everywhere and recreate the model and trainer. Do not change only one occurrence and assume the whole pipeline updated.

### The model output stops before the JSON closes

Increase `max_new_tokens` from 180 to 256 in `generate_answer`. Rerun both base and fine-tuned evaluations with the same value.

### The model wraps JSON in Markdown fences

That output fails this experiment's strict contract. Do not silently strip fences during scoring. Improving that behavior is part of fine-tuning. An application may add a separate repair layer, but repaired and strict metrics should be reported separately.

### Exact match is low but schema validity is high

The model learned the interface but not necessarily the incident mapping. Inspect category, service, severity, and action accuracy separately. Review whether the synthetic scenarios provide enough consistent evidence.

### The model performs well on random held-out rows but poorly here

Random rows from the same scenario can be near-duplicates. This tutorial splits by scenario specifically to make generalization harder and the result more informative.

### Colab disconnects

The generated data and completed metrics are on Drive. Training checkpoints are disabled to keep the workflow simple, so an interrupted training run may need to restart. After reconnecting, rerun cells in order and avoid overwriting previous result files until you have inspected them.

### Drive runs out of space

Keep the adapter and metrics, delete unneeded merged-model copies, and empty Drive trash if appropriate. Do not delete the adapter before verifying that it reloads.

## Limitations

This experiment has several important limits:

- The alerts are synthetic and template-derived.
- Twenty-five scenarios cannot represent real operational diversity.
- The severity and escalation rules are tutorial conventions.
- Exact-match metrics measure agreement with our targets, not objective root-cause truth.
- A 40-case behavioral subset is useful for a first run but too small for strong performance claims.
- High schema compliance does not make autonomous remediation safe.
- A model trained on this dataset should not be exposed to real production alerts with the expectation of reliable diagnosis.

The next useful iteration would add more diverse human-reviewed scenarios, paraphrases written independently of the templates, confusing multi-cause incidents, a larger held-out set, and a separate test of converted-model behavior.

## Conclusion

Colab supplies the temporary training environment; Unsloth supplies the model-loading and QLoRA workflow. The more important engineering work happens around them: defining a narrow contract, constructing inspectable data, separating scenarios across splits, evaluating the base model first, and validating every generated object.

The goal was not to build an autonomous site-reliability engineer. It was to test whether a small model could become a reliable component at one boundary of a larger system.

A decreasing loss curve shows that training happened. Held-out behavioral metrics show what the adapter actually learned.

## Official Documentation

- [Unsloth fine-tuning guide](https://unsloth.ai/docs/get-started/fine-tuning-llms-guide)
- [Unsloth troubleshooting and evaluation](https://unsloth.ai/docs/basics/troubleshooting-and-faqs)
- [Hugging Face TRL documentation](https://huggingface.co/docs/trl/index)
- [Google Colab](https://colab.research.google.com/)