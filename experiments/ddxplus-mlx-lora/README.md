# DDXPlus MLX LoRA experiment

A reproducible local workflow for teaching `Qwen2.5-1.5B-Instruct` a small differential-diagnosis response contract using English DDXPlus and MLX LM LoRA on a quantized base. It covers source-data verification, split isolation, held-out evaluation, adapter training, evidence ablation, independent fused-model evaluation, oMLX deployment, a real QwenPaw chat, and rollback.

**This is an educational machine-learning experiment on synthetic cases. It is not a clinical tool, medical advice, or evidence of real-patient performance. Do not use it to diagnose, triage, or recommend care.**

The observed run was **tested locally on Apple Silicon**. Peak memory and total training time were not measured; no particular memory capacity or total runtime is claimed.

## Observed results

All three final modes used all **490 held-out cases**, the same system prompt, greedy generation (`temperature=0.0`), and `max_tokens=220`.

| Metric | Base | Adapter | Dequantized fused |
|---|---:|---:|---:|
| Held-out cases | 490 | 490 | 490 |
| Top-1 accuracy | 10.41% | 92.65% | 92.86% |
| Top-3 accuracy | 12.86% | 97.14% | 97.14% |
| Structured-response rate | 0.00% | 99.80% | 99.80% |
| Mean reference overlap@3 | 0.206 / 3 | 2.043 / 3 | 2.049 / 3 |

Common test-set SHA-256:

```text
c5a5b94a3377c78b2ac1209899ca6e8d1df3a9aa25ce0a2e26ad33373f6c5838
```

Top-1 compares the parsed most-likely label with the dataset label. Top-3 checks whether that label appears in the predicted differential. Structured-response rate is a strict format check, separate from tolerant label extraction. Reference overlap@3 is the intersection size between predicted and source-supplied reference labels; it is not clinical agreement.

Base-to-adapter comparison: 440 top-1 disagreements, 404 incorrect-to-correct improvements, one correct-to-incorrect regression, and 50 unchanged top-1 labels.

### Fusion is not exact equivalence

The original quantized fused artifact was rejected after its independent 490-case evaluation scored **16.94% top-1, 23.88% top-3, 0.00% structured responses, and 0.335 mean overlap@3**. It was not deployed.

A separate `mlx_lm.fuse --dequantize` artifact produced the final fused column. It matched the adapter on **486/490 complete responses** and **489/490 top-1 labels**. Strict identity failed. All four differences were saved and inspected: three change only the differential, while `test-0297` changes top-1 from incorrect `Unstable angina` to the dataset label `Stable angina`.

Deployment used the explicit `reviewed_with_differences` gate: at most 2% differing responses and at most 0.01 absolute top-1 accuracy change. The observed rates were 0.8163% and 0.002041 respectively. This is threshold acceptance after difference review, **not exact behavioral equivalence or clinical validation**. The full adapter was not overwritten or retrained to obtain these results.

## Requirements

- An Apple Silicon Mac with Git, `uv`, `curl`, `unzip`, `rsync`, `jq`, and Swift command-line tools.
- Python 3.11 through `uv` for the experiment environment.
- Sufficient disk space for the official data, base model, adapter checkpoints, and fused artifacts. The original 10GB estimate is not a measured upper bound.
- Existing oMLX and QwenPaw installations only for the deployment stages.
- Permission to restart the actual system LaunchDaemons through `sudo launchctl` for those stages. Homebrew services are not used.

Pinned experiment dependencies are in `requirements.txt`. The observed service versions were oMLX 0.7.0 and QwenPaw 2.2.2; the QwenPaw helper used its installed Python 3.12.15. See `results/public/software-versions.json` for the recorded experiment versions.

## Repository layout

```text
experiments/ddxplus-mlx-lora/
├── prepare_ddxplus.py          # Official-split sampling and evidence decoding
├── evaluate.py                 # Identical-case generation and metrics
├── analyze_results.py          # Comparisons and selected qualitative examples
├── evidence_ablation.py        # Non-initial Symptoms-section ablation
├── verify_fusion.py            # Full-run identity and deployment gates
├── deploy_omlx.py              # Checksum-bound oMLX deployment
├── qwenpaw_model.py            # Scoped selection, backup, and rollback
├── qwenpaw_provider_state.py   # Existing QwenPaw provider API integration
├── artifact_identity.py        # Artifact hashes and runtime identity
├── audit_run.py                # Recomputation from preserved local evidence
├── make_assets.py              # Source-derived article figures
├── package_results.py          # Bounded, non-sensitive public summaries
└── results/public/             # Reviewed metrics and selected examples only
```

Datasets, generated JSONL, weights, adapters, fused models, virtual environments, raw API payloads, logs, service state, and article screenshots are excluded by `.gitignore`.

## Reproduce the experiment

Run stages in order. Commands assume the experiment directory shown below. Existing evaluation responses require `--resume`; existing adapter and fused destinations are deliberately not overwritten. Inspect valid existing artifacts and reuse them rather than repeating expensive stages.

### 1. Fetch the companion and create the environment

```bash
set -euo pipefail
command -v uv >/dev/null
command -v git >/dev/null

if [ ! -f "$HOME/night-thoughts/experiments/ddxplus-mlx-lora/experiment_config.py" ]; then
  if [ -e "$HOME/night-thoughts" ]; then
    echo "The repository exists but the companion is missing; inspect it first."
    exit 1
  fi
  git clone --filter=blob:none --sparse \
    https://github.com/hslimi/night-thoughts.git \
    "$HOME/night-thoughts"
  git -C "$HOME/night-thoughts" sparse-checkout set \
    experiments/ddxplus-mlx-lora
fi

cd "$HOME/night-thoughts/experiments/ddxplus-mlx-lora"
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
mkdir -p raw data evaluation results/logs adapters fused
```

### 2. Download and verify official English DDXPlus

Sources: [official Figshare record](https://figshare.com/articles/dataset/DDXPlus_Dataset_English_/22687585), [versioned DOI](https://doi.org/10.6084/m9.figshare.22687585.v2), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

```bash
set -euo pipefail
cd "$HOME/night-thoughts/experiments/ddxplus-mlx-lora"
source .venv/bin/activate
exec > >(tee -a results/logs/part1.log) 2>&1
cd raw

download() {
  if [ ! -f "$2" ]; then
    curl --fail --location --retry 3 "$1" --output "$2"
  else
    echo "Reusing downloaded file: $2"
  fi
}

verify_md5() {
  actual=$(md5 -q "$1")
  if [ "$actual" != "$2" ]; then
    echo "MD5 mismatch for $1: expected $2, got $actual"
    exit 1
  fi
  echo "Verified: $1"
}

download https://ndownloader.figshare.com/files/40278013 release_evidences.json
download https://ndownloader.figshare.com/files/62561569 release_conditions.json
download https://ndownloader.figshare.com/files/40278019 release_train_patients.zip
download https://ndownloader.figshare.com/files/40278022 release_validate_patients.zip
download https://ndownloader.figshare.com/files/40278016 release_test_patients.zip

verify_md5 release_evidences.json 0660962abe0bbf99e1fb77188c253597
verify_md5 release_conditions.json a992eadcff3099dd72e1820fbd2115aa
verify_md5 release_train_patients.zip f75a78420ccb061951daa4db2d62139b
verify_md5 release_validate_patients.zip e4db88e9082f18410de6fd0cb7e74d18
verify_md5 release_test_patients.zip 6fd53d331cf19ed4439bf4f46b92ee94

for split in train validate test; do
  archive="release_${split}_patients.zip"
  member="release_${split}_patients"
  unzip -Z1 "$archive" | grep -Fx "$member" >/dev/null
  unzip -oq "$archive" "$member"
  test -s "$member"
done
```

The patient members are CSV-formatted but extensionless. The code reads `release_train_patients`, `release_validate_patients`, and `release_test_patients`, not invented `.csv` names. Verified official row counts are 1,025,602 train, 132,448 validation, and 134,529 test. There are 223 evidence definitions and 49 pathology labels.

### 3. Generate and check the isolated splits

```bash
set -euo pipefail
cd "$HOME/night-thoughts/experiments/ddxplus-mlx-lora"
source .venv/bin/activate
exec > >(tee -a results/logs/part2.log) 2>&1
python prepare_ddxplus.py
python - <<'PY'
import json
from collections import Counter
from pathlib import Path
from experiment_config import verify_test_cases

prompt_sets = {}
for split, expected in {"train": 1960, "valid": 490, "test": 490}.items():
    records = [json.loads(line) for line in Path(f"data/{split}.jsonl").read_text().splitlines()]
    assert len(records) == expected
    prompt_sets[split] = {record["messages"][1]["content"] for record in records}
    assert len(prompt_sets[split]) == expected
assert not prompt_sets["train"] & prompt_sets["valid"]
assert not prompt_sets["train"] & prompt_sets["test"]
assert not prompt_sets["valid"] & prompt_sets["test"]
cases = [json.loads(line) for line in Path("evaluation/test_cases.jsonl").read_text().splitlines()]
counts = Counter(case["ground_truth"] for case in cases)
assert len(cases) == len({case["case_id"] for case in cases}) == 490
assert len(counts) == 49 and set(counts.values()) == {10}
print(f"test_cases_sha256: {verify_test_cases()}")
PY
```

Sampling stays inside each official split with seed 42: 40 cases per pathology for train and 10 each for validation and test. Duplicate decoded prompts are replaced by other eligible rows from the same split and class. Official test rows are never moved into training.

CSV list fields are decoded with `ast.literal_eval`, never `eval`. Numeric evidence values retain their decoded meanings; categorical `N` becomes `No`. Symptoms and antecedents remain separate.

One source-data edge case is preserved: `Larygospasm` has two usable reference labels in the selected validation and test cases. Training targets have three source-derived labels; validation/test targets permit two rather than inventing another. The system prompt still requests three predicted labels, and the strict format metric requires three. A two-label prediction therefore does not pass that metric. Ten held-out cases have two reference labels, which limits their possible reference overlap.

The preprocessing command verifies and reuses a complete set of valid generated files. Incomplete files or mismatches in metadata, structure, split isolation, or the pinned test hash stop the command. Overwriting requires inspecting the files and explicitly passing `--overwrite-generated`; that flag was not used for this run.

The generated test set and `evaluation/metadata.json` are intentionally excluded from Git. Regenerate them to use the pinned `evaluation/test_cases.sha256` sidecar. The preprocessing script refuses a different generated test set rather than silently mixing experiments.

### 4. Smoke-test generation and evaluate the base model

```bash
set -euo pipefail
cd "$HOME/night-thoughts/experiments/ddxplus-mlx-lora"
source .venv/bin/activate
exec > >(tee -a results/logs/part3.log) 2>&1
python evaluate.py --mode base --limit 3 --output-prefix results/base-smoke
python evaluate.py --mode base --limit 0
```

The three-case smoke test is not a benchmark. The base/adapter comparison runs after adapter evaluation in the next stages.

The evaluator pins base revision `8b403126fc14f14cfc99bb4cfa72ecbc129ea677` and records model/adapter file hashes, evaluator and prompt-metadata hashes, and runtime versions. It uses greedy generation for every mode. The default `--limit 100` is a smoke/development setting; final runs must explicitly use `--limit 0`.

The recorded training configuration names the upstream model ID. Evaluation and fusion verification bind the preserved artifacts to the pinned snapshot; artifact identity was backfilled later from those artifacts, not captured during original generation. This provenance boundary is recorded rather than presented as contemporaneous telemetry.

### 5. Smoke-test training and train the full adapter

The following preserves the original training configuration while correcting fresh reproduction to use the pinned local model snapshot for training and fusion. The saved original training configuration names the upstream hub ID; no new training run was performed to rewrite that record. Do not rerun over the preserved full adapter or replace its full training log.

```bash
set -euo pipefail
cd "$HOME/night-thoughts/experiments/ddxplus-mlx-lora"
source .venv/bin/activate
exec > >(tee -a results/logs/part4.log) 2>&1
MODEL="mlx-community/Qwen2.5-1.5B-Instruct-4bit"
BASE_MODEL="$(python -c 'from artifact_identity import pinned_base_path; print(pinned_base_path())')"
export MODEL

if [ -e adapters/smoke ] || [ -e adapters/ddxplus ]; then
  echo "An adapter destination exists; inspect and preserve it before training."
  exit 1
fi

if [ -e results/logs/part4-train-full.log ]; then
  echo "A full training log exists; inspect and preserve it before training."
  exit 1
fi

mlx_lm.lora \
  --model "$BASE_MODEL" --train --data data \
  --fine-tune-type lora --adapter-path adapters/smoke \
  --batch-size 2 --grad-accumulation-steps 4 --num-layers 8 \
  --iters 2 --learning-rate 1e-5 --max-seq-length 2048 \
  --steps-per-report 1 --steps-per-eval 1 --save-every 2 \
  --mask-prompt --grad-checkpoint --seed 42

test -s adapters/smoke/adapters.safetensors

mlx_lm.lora \
  --model "$BASE_MODEL" --train --data data \
  --fine-tune-type lora --adapter-path adapters/ddxplus \
  --batch-size 2 --grad-accumulation-steps 4 --num-layers 8 \
  --iters 1200 --learning-rate 1e-5 --max-seq-length 2048 \
  --steps-per-report 10 --steps-per-eval 200 --save-every 200 \
  --mask-prompt --grad-checkpoint --seed 42 \
  2>&1 | tee results/logs/part4-train-full.log

test -s adapters/ddxplus/adapters.safetensors
python evaluate.py --mode adapter --limit 0
python analyze_results.py --compare base-adapter
```

Actual full-run configuration: LoRA on eight layers of the quantized base, rank 8, scale 20.0, dropout 0.0, Adam, batch size 2, gradient accumulation 4, 1,200 iterations, learning rate `1e-5`, maximum sequence length 2048, prompt masking, gradient checkpointing, and seed 42. The batch-size-one fallback was **not** used. If memory pressure requires it, use batch size 1 and record that as a different configuration; do not attribute those results to this run.

First reported training loss: **2.056 at iteration 10**. Final training loss: **0.057 at iteration 1,200**. Validation loss: **2.257 at iteration 1**, **0.144 at iteration 200**, and **0.064 at iteration 1,200**. The iteration-one validation measurement is not an initial training-loss report. The two-iteration smoke adapter and its losses are separate from these final values.

### 6. Inspect examples and run the evidence ablation

```bash
set -euo pipefail
cd "$HOME/night-thoughts/experiments/ddxplus-mlx-lora"
source .venv/bin/activate
exec > >(tee -a results/logs/part5.log) 2>&1
python analyze_results.py --compare base-adapter
python evidence_ablation.py --case-id test-0002 \
  --finding 'Do you have symptoms that are increased with physical exertion but alleviated with rest? Yes.'
```

The ablation removes a finding from **Symptoms**, excludes the initial-evidence bullet, and retains the initial evidence. It does not use a prompt-wide regular expression that could remove the wrong section.

For `test-0002`, it removed “Do you have symptoms that are increased with physical exertion but alleviated with rest? Yes.” The adapter returned exactly the same response before and after removal: top-1 `Unstable angina`, with `Possible NSTEMI / STEMI` and `Stable angina` in the differential. The original dataset label was `Stable angina`; **no new ground truth is assigned to the edited case**.

Selected genuine examples in `results/public/qualitative-examples.json`:

- `test-0001`: base `Chronic rhinosinusitis` → adapter `Anemia`, matching the dataset label.
- `test-0000`: shared top-1 failure—base `Acute laryngitis`, adapter `Viral pharyngitis`, dataset label `URTI`.
- `test-0002`: structured but incorrect adapter top-1 `Unstable angina` instead of `Stable angina`.

### 7. Fuse and independently evaluate

Do not remove the existing fused directories. The rejected quantized artifact is retained for audit, and the corrected artifact has a separate destination.

```bash
set -euo pipefail
cd "$HOME/night-thoughts/experiments/ddxplus-mlx-lora"
source .venv/bin/activate
exec > >(tee -a results/logs/part6.log) 2>&1
MODEL="mlx-community/Qwen2.5-1.5B-Instruct-4bit"
BASE_MODEL="$(python -c 'from artifact_identity import pinned_base_path; print(pinned_base_path())')"
ADAPTER="adapters/ddxplus"
FUSED="fused/ddxplus-qwen-dequantized"
export MODEL ADAPTER FUSED

if [ -e "$FUSED" ]; then
  echo "The fused destination exists; inspect and preserve it."
  exit 1
fi

mlx_lm.fuse \
  --model "$BASE_MODEL" --adapter-path "$ADAPTER" \
  --save-path "$FUSED" --dequantize

test -f "$FUSED/config.json"
test -f "$FUSED/tokenizer.json"
python evaluate.py --mode fused --limit 0 \
  --output-prefix results/fused-dequantized-full
python analyze_results.py --compare adapter-fused \
  --fused-prefix fused-dequantized-full
python verify_fusion.py \
  --fused-prefix fused-dequantized-full --model-path "$FUSED"
```

A strict mismatch stops this command. Inspect **all** entries in `results/fused-dequantized-full-response-differences.json`. Only after that review, the documented threshold gate is:

```bash
python verify_fusion.py \
  --fused-prefix fused-dequantized-full \
  --model-path fused/ddxplus-qwen-dequantized \
  --accept-reviewed-differences
```

Do not use this flag to conceal an unreviewed discrepancy. `verify_fusion.py` binds the review to the corresponding run metadata, artifact hashes, 490-case test file, and generation settings. Deployment repeats those checks with explicit runtime exceptions rather than relying on `assert`.

### 8. Deploy to oMLX and verify QwenPaw

The deployment helper copies only the reviewed dequantized artifact to `~/.omlx/models/ddxplus-qwen/`. It refuses to overwrite different files, discovers the exact ID through `/v1/models`, and sends a real held-out request. It does not modify unrelated model registrations or use Homebrew services. The forced restart briefly interrupts oMLX-served models and active requests.

```bash
set -euo pipefail
cd "$HOME/night-thoughts/experiments/ddxplus-mlx-lora"
source .venv/bin/activate
exec > >(tee -a results/logs/part7.log) 2>&1
python deploy_omlx.py --case-id test-0001
```

The helper runs `sudo launchctl kickstart -k system/com.omlx.server`. After an authorized manual restart, use `python deploy_omlx.py --case-id test-0001 --skip-restart` to verify the running daemon instead.

The observed discovered ID was `ddxplus-qwen`; it was discovered, not guessed. Direct oMLX returned `Anemia` for `test-0001`, matching that synthetic case's original dataset label.

If the existing saved QwenPaw credential is stale, the explicitly permanent synchronization used in this run was:

```bash
cd "$HOME/night-thoughts/experiments/ddxplus-mlx-lora"
"$HOME/.qwenpaw/venv/bin/python" qwenpaw_provider_state.py --sync-current-key
"$HOME/.qwenpaw/venv/bin/python" qwenpaw_provider_state.py --verify-current-key
```

This reads the current key from oMLX's local settings and updates the saved oMLX provider through QwenPaw's installed API. It never prints or saves the key in a result file. The URL, protocol, and unrelated settings are preserved. Inspection of the installed QwenPaw 2.2.2 code shows that `auto_discover: false` is request-scoped: it suppresses a post-save discovery refresh and is not persisted provider configuration. **This is a persistent credential repair: rollback intentionally does not restore the stale key.**

Select the discovered model for the default agent, preserving the global selection and unrelated providers:

```bash
python qwenpaw_model.py --agent-id default
python - <<'PY'
import json
from pathlib import Path
metadata = json.loads(Path("evaluation/metadata.json").read_text())
case = next(
    json.loads(line)
    for line in Path("evaluation/test_cases.jsonl").read_text().splitlines()
    if json.loads(line)["case_id"] == "test-0001"
)
Path("results/qwenpaw-console-message.txt").write_text(
    metadata["system_prompt"] + "\n\n" + case["prompt"]
)
PY
```

Open the existing QwenPaw console at `http://localhost:8088/chat`, start a clean chat, select the experiment model, and submit the saved prompt. A health check is not a chat verification. Preserve the genuine response and the model-selection evidence before rollback.

The observed QwenPaw round trip succeeded but returned `Acute dystonic reactions`, not `Anemia`, and differed from direct oMLX. Agent context and existing generation settings may contribute; this check does not isolate the cause. This was an incorrect transport-check response, not a benchmark or direct-equivalence test; zero prompt retries were used to seek a better answer.

### 9. Roll back QwenPaw

Before selection, the helper saves the global and selected-agent configurations and original provider model state. Rollback refuses to overwrite independently changed configuration.

```bash
set -euo pipefail
cd "$HOME/night-thoughts/experiments/ddxplus-mlx-lora"
source .venv/bin/activate
exec > >(tee -a results/logs/part8.log) 2>&1
python qwenpaw_model.py --prepare-rollback
sudo launchctl kickstart -k system/com.qwenpaw.app
python qwenpaw_model.py --verify-rollback
```

The actual system daemon must be restarted after preparation; the verifier checks its process start time. This forced restart briefly interrupts QwenPaw sessions and active requests. Rollback restores original global and per-agent selections, exact configuration backups, and provider registrations/removal state. Only discovery timestamps and capability provenance may refresh.

In the observed run, **Restore default model** in the experiment chat also cleared its per-chat override without generating another response. The original response remained visible. QwenPaw finished in its original pre-experiment model configuration, with the explicitly requested permanent credential repair retained. The adapter, local fused artifacts, and deployed oMLX model were retained; the optional deployed-model removal block was not run.

## Resume and audit

For interrupted or completed evaluation files, add `--resume`. The evaluator checks the case prefix, artifact and software identity, prompt metadata, evaluation contract, and generation settings before reusing responses. A completed run returns before loading a model:

```bash
source .venv/bin/activate
python evaluate.py --mode base --limit 0 --resume
python evaluate.py --mode adapter --limit 0 --resume
python evaluate.py --mode fused --limit 0 \
  --output-prefix results/fused-dequantized-full --resume
```

The rejected artifact, if deliberately revalidated, needs `FUSED=fused/ddxplus-qwen` and its own `--output-prefix results/fused`. Do not relabel its results as the corrected fused model. The guarded training and fusion commands do not automatically resume partial artifacts; inspect saved checkpoints rather than overwriting them.

The full local audit requires the private run artifacts, official raw files, generated splits, model snapshots, deployment evidence, QwenPaw backups, and the running restored QwenPaw service:

```bash
python audit_run.py --require-rollback
```

It recomputes metrics from every saved response, rebuilds all 490 test prompts and targets from official rows, checks source checksums and split isolation, verifies training-log losses and fusion comparisons, and confirms configuration rollback and permanent credential synchronization. It does not generate new benchmark responses. Its local report may contain private configuration details and is therefore not committed.

After a successful local audit, `python package_results.py` regenerates only bounded public summaries under `results/public/`. This packaging step needs the private evidence and is not a substitute for running the experiment. `results/public/provenance.json` binds public files to source-code and source-evidence hashes.

The repository has no existing automated test suite. Verification consists of source compilation, the real end-to-end stages above, full-response recomputation, and inspected genuine outputs. Smoke tests are never substitutes for the 490-case evaluations.

## Article figures

`article-assets/manifest.json` maps each working PNG to its supporting result or log. Ten figures are source-derived visualizations of real outputs; they are not presented as terminal screenshots. The QwenPaw figure uses two unmodified crops from one genuine console capture. Loss curves are generated only from `results/logs/part4-train-full.log`.

```bash
source .venv/bin/activate
python make_assets.py --stage dataset
python make_assets.py --stage loss
python make_assets.py --stage evaluation
python make_assets.py --stage fused
python make_assets.py --stage qualitative
python make_assets.py --stage ablation
python make_assets.py --stage omlx
python make_assets.py --stage qwenpaw
```

The QwenPaw stage requires the real capture crops under `article-assets/work/`; it does not create a mock interface. `render_svg.swift` can render a generated SVG at its declared width and height, for example:

```bash
swift render_svg.swift article-assets/01-training-loss.svg \
  1500 1030 article-assets/01-training-loss.png
```

Use the dimensions declared in each SVG. GUI or Screen Recording permission failures must be reported; do not replace a failed capture with illustrative output. Review crops for credentials, account identity, private paths, usernames, unrelated desktop content, and identifying hardware details before using them. Screenshots and raw logs are not committed here.

## Public evidence map

| File | Contents |
|---|---|
| `base.summary.json`, `adapter.summary.json`, `fused-dequantized.summary.json` | Final 490-case summaries |
| `fused-quantized-rejected.summary.json` | Clearly named rejected fusion |
| `training-config.json`, `training-losses.json` | Actual configuration and log-derived losses |
| `base-adapter-comparison.json` | Full base/adapter comparison |
| `adapter-fused-dequantized-comparison.json` | Full corrected-fusion comparison |
| `adapter-fused-quantized-rejected-comparison.json` | Rejected-fusion comparison |
| `fused-dequantized-deployment-review.json` | Identity, limits, and non-equivalence status |
| `fused-response-differences.json` | All four reviewed response differences |
| `qualitative-examples.json` | Selected synthetic improvement and failures |
| `evidence-ablation.json` | Original/ablated prompts and responses; no edited-case label |
| `deployment-verification.json` | Sanitized oMLX/QwenPaw outputs and rollback status |
| `run-observations.json` | Checksums, split counts, provenance, and resume observations |
| `software-versions.json` | Recorded software and scoped hardware description |
| `provenance.json` | Public-file, source-code, and source-evidence hashes |

Full evaluation JSONL, generated datasets, raw API payloads, private service configuration, account inspection, local logs, credentials, screenshots, model weights, adapters, and fused models are not included.

## Attribution and licensing

This experiment adapts **DDXPlus Dataset English** by **Tchango et al.**, released under **CC BY 4.0**:

- [Official dataset](https://figshare.com/articles/dataset/DDXPlus_Dataset_English_/22687585)
- [DOI: 10.6084/m9.figshare.22687585.v2](https://doi.org/10.6084/m9.figshare.22687585.v2)
- [DDXPlus paper, arXiv:2205.09148](https://arxiv.org/abs/2205.09148)

Changes include decoding evidence into English, formatting chat examples, deterministic stratified subset selection with duplicate-prompt replacement, and constructing ranked targets from supplied labels without inventing a missing third label. Curated synthetic case excerpts retain this attribution. DDXPlus data and generated datasets are not redistributed as full files here.

The upstream [Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct) model is licensed under [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0). This run used the [MLX Community 4-bit conversion](https://huggingface.co/mlx-community/Qwen2.5-1.5B-Instruct-4bit). Model weights are not included. The repository currently has no general root license; this experiment does not assert a new repository-wide license or change the dataset/model licenses.

## Limitations

- DDXPlus patients are synthetic; these results do not establish clinical usefulness or real-patient performance.
- The closed set contains 49 labels. Real patients may have multiple conditions, incomplete histories, or conditions outside that set.
- Stratified sampling does not preserve original prevalence.
- Reference-differential overlap is not clinician agreement or clinical validation.
- Fluent structure is not correctness; the adapter still has failures and the selected ablation response is unchanged.
- Edited cases have no newly validated ground truth.
- Fused inference is numerically different in four cases; reviewed threshold acceptance is not exact equivalence.
- QwenPaw adds agent context and existing settings. Its incorrect chat response is not a controlled model benchmark.
- No peak-memory measurement, total-training-time claim, or compatibility claim for a particular memory size is made.
