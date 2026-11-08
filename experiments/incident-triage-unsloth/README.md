# Incident triage with Colab, Unsloth, and QLoRA

This experiment tests whether a small instruction model can learn to convert synthetic incident alerts into strict JSON that an application can validate and route. It compares `unsloth/Qwen2.5-1.5B-Instruct` before and after QLoRA fine-tuning on the same 40 held-out alerts.

The completed run used 200 optimizer steps. The adapter improved JSON and schema validity from 0.00% to 100.00%, but exact-match and summary accuracy remained 0.00%. It therefore learned the output interface much better than the complete incident-label mapping.

The model does not execute remediation commands or diagnose real infrastructure. All alerts are synthetic and template-derived.

## Output JSON contract

Every prediction must contain exactly these six fields:

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

- `service`: `payments-api`, `authentication`, `search`, `inventory`, `notifications`, or `unknown`.
- `severity`: `sev1`, `sev2`, `sev3`, or `sev4`.
- `category`: `database_capacity`, `deployment_regression`, `authentication`, `network`, or `unknown`.
- `next_action`: `inspect_database_connections`, `inspect_recent_deployment`, `inspect_auth_configuration`, `inspect_network_path`, or `request_more_context`.
- `summary`: a short, non-empty string.
- `escalate`: a JSON boolean. The tutorial convention escalates `sev1` and `sev2` only.

Strict JSON scoring rejects Markdown fences, prose, missing or additional keys, invalid types, and values outside the allowed vocabularies. Invalid outputs also count as failures for exact match and every field-accuracy metric. Application-side validation is still required after fine-tuning.

## Dataset and split methodology

The deterministic generator uses seed `3407`, 25 manually defined scenarios, random metric values, optional prefixes and suffixes, and a unique incident reference for every alert.

| Split | Scenarios | Examples | Examples per category |
|---|---:|---:|---:|
| Training | 15 | 1,500 | 300 |
| Validation | 5 | 400 | 80 |
| Test | 5 | 400 | 80 |

All 2,300 alerts are unique. Scenario IDs do not overlap between splits, and every split contains all five categories. Splitting by scenario rather than by row prevents near-duplicate variants of one incident template from appearing in both training and test data.

Behavioral evaluation uses the first eight test records from each alphabetically sorted unseen test scenario: 40 cases total. The base and fine-tuned prediction files contain identical alerts in the same order. The other 360 generated test cases were not behaviorally evaluated in this run.

## Actual hardware and software environment

- GPU: NVIDIA RTX PRO 6000 Blackwell Server Edition, 101,974,081,536 bytes of VRAM (approximately 102 GB).
- Python: 3.13.16 on Linux 6.6.159+ x86_64 with glibc 2.39.
- PyTorch: 2.11.0+cu130; `torch.version.cuda` 13.0; bf16 supported.
- Unsloth and Unsloth Zoo: 2026.10.10.
- Transformers: 5.17.0; TRL: 1.15.0; PEFT: 0.21.2.
- Datasets: 4.8.5; Accelerate: 1.15.0; bitsandbytes: 0.50.2.
- pandas: 2.2.3; Matplotlib: 3.10.0; xformers: 0.0.35.

`requirements-freeze.txt` and `results/run-metadata.json` record these direct package versions. The freeze file documents this runtime; it is not a portable installation lock for a different CUDA environment.

Unsloth reported that xformers 0.0.35 was built for PyTorch 2.10.0+cu128 while the runtime used 2.11.0+cu130. It used PyTorch attention instead. No xformers reinstall was required. Generation also warned that `max_new_tokens=180` took precedence over the model's larger `max_length`; output was not truncated, so 180 remained unchanged for both evaluations.

## Reproduction instructions

The executed notebook is the canonical end-to-end record, including outputs. The stage scripts organize the same logic for reuse.

1. Open the [Colab notebook](https://colab.research.google.com/drive/1OddUYZZdb5dpmVr2bQVH2mfwVaD9ujzR) and select a GPU runtime.
2. Mount Google Drive and create `/content/drive/MyDrive/nightthoughts-incident-triage` with `data`, `results`, and `adapter` subdirectories.
3. Install and import Unsloth. For a fresh reproduction, run the notebook cells in order rather than rerunning only later cells against an unknown runtime state.
4. Generate and inspect the JSONL data. The standalone equivalent is:

   ```bash
   INCIDENT_TRIAGE_DATA_DIR=data python3 src/dataset_generation.py
   ```

5. Run the base evaluation before attaching or loading an adapter:

   ```bash
   python3 src/evaluate.py --mode base
   ```

6. Train and save the adapter:

   ```bash
   python3 src/train.py
   ```

7. Evaluate the saved adapter on the same fixed subset:

   ```bash
   python3 src/evaluate.py --mode finetuned
   ```

8. Regenerate the CSV and loss diagram without smoothing or adding validation points:

   ```bash
   python3 src/plot_losses.py \
     --log-history results/trainer-log-history.json \
     --output-dir results
   ```

The training and evaluation scripts require a compatible GPU environment. They default to the Drive project path above; set `INCIDENT_TRIAGE_PROJECT_DIR` to use another project directory. Preserve completed result files before rerunning so that a different dataset, adapter, subset, or configuration cannot silently replace them.

## Training configuration

- Base model: `unsloth/Qwen2.5-1.5B-Instruct`, loaded with `load_in_4bit=True`.
- Maximum sequence length: 1,024 tokens.
- LoRA rank and alpha: 16 each; dropout 0; bias `none`.
- Target modules: `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.
- Optimizer steps: 200; warmup steps: 10.
- Per-device training batch size: 2; gradient accumulation: 4; effective batch size: 8.
- Per-device evaluation batch size: 4.
- Learning rate: `2e-4` with a linear scheduler.
- Optimizer: `adamw_8bit`; weight decay: 0.01.
- Training loss logged every 5 steps; validation loss evaluated every 50 steps.
- Seed: 3407; checkpoints disabled; reporting disabled.
- Trainer `train_runtime`: 107.3805 seconds; total Colab training-cell time: 111.204 seconds.

Most quantized base weights remain frozen. LoRA adds trainable low-rank matrices, and only adapter parameters are updated. Rank `r=16` controls those matrices' inner dimension. Gradient accumulation combines four micro-batches per optimizer step. QLoRA reduces memory requirements; it does not guarantee better task accuracy.

## Actual baseline and fine-tuned metrics

Values come from `results/base_metrics.json` and `results/finetuned_metrics.json`. Changes are absolute percentage points, not relative improvements.

| Metric | Base | Fine-tuned | Absolute change |
|---|---:|---:|---:|
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

The base model commonly wrapped otherwise readable objects in Markdown fences. Strict scoring therefore produced zero baseline rates; these rates must not be interpreted as a fence-stripped semantic evaluation.

No fine-tuned case matched all six target fields exactly. A genuine partial success is `INC-02222` in `unknown_worker_saturation`: service, severity, category, next action, and escalation matched, while the generated summary did not. In contrast, `INC-02061` was schema-valid but received the wrong severity, category, and escalation. See the saved predictions for the exact outputs.

## Loss and behavioral interpretation

Training loss fell from 3.045980 at step 5 to 0.051658 at step 200. It dropped sharply through step 50 and then mostly plateaued around 0.05–0.07 with minor fluctuations.

Validation loss moved in the opposite direction at all four measured checkpoints:

| Optimizer step | Validation loss |
|---:|---:|
| 50 | 0.631923 |
| 100 | 0.756127 |
| 150 | 0.808638 |
| 200 | 0.838244 |

Training and validation losses are logged at different steps; the CSV leaves the other column blank where no measurement exists. The diagram plots only real log entries. The sustained train/validation divergence is consistent with worsening generalization, although four validation points and one run do not prove a general overfitting diagnosis. Adding steps is not justified by this run alone.

Loss measures token prediction during training and validation. It does not directly measure whether complete output parses as JSON, follows the schema, or agrees with incident labels. The behavioral results show the distinction clearly: 100.00% schema validity coexists with 0.00% exact match.

The adapter learned strong structural compliance, high service accuracy, and perfect unknown-category recall on the eight ambiguous test cases. Category accuracy was 60.00%, but severity reached only 42.50%, and summaries never exactly matched the tutorial wording. Both `auth_key_rotation` and `deploy_migration_errors` had 0/8 correct categories; `db_deadlock_payments`, `network_ipv6_route`, and `unknown_worker_saturation` had 8/8. Valid JSON is therefore not evidence of a correct diagnosis.

## Repository structure

```text
.
├── README.md
├── incident-triage-unsloth.ipynb
├── requirements-freeze.txt
├── src/
│   ├── dataset_generation.py
│   ├── incident_contract.py
│   ├── train.py
│   ├── evaluate.py
│   └── plot_losses.py
├── data/
│   ├── train.jsonl
│   ├── validation.jsonl
│   └── test.jsonl
├── results/
│   ├── base_metrics.json
│   ├── base_predictions.json
│   ├── finetuned_metrics.json
│   ├── finetuned_predictions.json
│   ├── loss-history.csv
│   ├── loss-diagram.png
│   ├── trainer-log-history.json
│   ├── run-metadata.json
│   └── schema-validation-demo.json
└── screenshots/
    └── 01-gpu-runtime.png ... 16-adapter-saved.png
```

`results/schema-validation-demo.json` verifies two application-side paths: a schema-valid unknown category returns `request_more_context`, and fenced invalid output returns `manual_review`. The adapter was also reloaded successfully from Drive. No Part 15 merged-model export or Part 16 Apple Silicon/MLX conversion was performed.

## Known limitations

- Alerts are synthetic and template-derived; 25 scenarios cannot represent real operational diversity.
- The behavioral subset contains only 40 cases, eight per unseen test scenario. It cannot support strong real-world performance claims or stable estimates for uncommon failures.
- Agreement with tutorial labels is not proof of real-world incident-diagnosis accuracy. Severity, escalation, and action mappings are tutorial conventions.
- Exact summary matching measures wording agreement, not whether every paraphrase is operationally useful. Some valid summaries may still invent unsupported details and must be inspected.
- Unknown-category recall covers only eight template-derived ambiguous cases.
- Baseline field rates are affected by strict rejection of fenced output; no separate repair-layer evaluation was performed.
- Only the adapter reload and application-side schema paths were verified. Converted-model behavior was not tested.
- Schema compliance does not make autonomous remediation safe.

## Links and Drive artifacts

- [Executed Colab notebook](https://colab.research.google.com/drive/1OddUYZZdb5dpmVr2bQVH2mfwVaD9ujzR)
- [Hashnode draft](https://nightthoughts.me/preview/6ae2c96e98e231491b5e4841)
- [GitHub experiment folder](https://github.com/hslimi/night-thoughts/tree/main/experiments/incident-triage-unsloth)
- Drive project: `/content/drive/MyDrive/nightthoughts-incident-triage`
- Drive results: `/content/drive/MyDrive/nightthoughts-incident-triage/results`
- Drive adapter: `/content/drive/MyDrive/nightthoughts-incident-triage/adapter`

**Model weights, adapter binaries, merged models, checkpoints, caches, credentials, and other Drive artifacts are not committed.** The adapter remains only in Google Drive. The metadata helper uses `Path(ADAPTER_DIR).iterdir()` because the tutorial's reload snippet stores `ADAPTER_DIR` as a string; this did not change the dataset, model, subset, or training configuration.
