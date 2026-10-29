import json
import os
from pathlib import Path

import torch
from datasets import Dataset
from trl import SFTConfig, SFTTrainer
from unsloth import FastLanguageModel

from incident_contract import training_messages

PROJECT_DIR = Path(os.environ.get(
    "INCIDENT_TRIAGE_PROJECT_DIR",
    "/content/drive/MyDrive/nightthoughts-incident-triage",
))
DATA_DIR = PROJECT_DIR / "data"
RESULTS_DIR = PROJECT_DIR / "results"
ADAPTER_DIR = PROJECT_DIR / "adapter"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
ADAPTER_DIR.mkdir(parents=True, exist_ok=True)

MAX_SEQ_LENGTH = 1024
BASE_MODEL = "unsloth/Qwen2.5-1.5B-Instruct"


def load_records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


train_records = load_records(DATA_DIR / "train.jsonl")
validation_records = load_records(DATA_DIR / "validation.jsonl")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=MAX_SEQ_LENGTH,
    dtype=None,
    load_in_4bit=True,
)


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

model.save_pretrained(str(ADAPTER_DIR))
tokenizer.save_pretrained(str(ADAPTER_DIR))
with (RESULTS_DIR / "trainer-log-history.json").open("w", encoding="utf-8") as handle:
    json.dump(trainer.state.log_history, handle, indent=2)
with (RESULTS_DIR / "training-stats.json").open("w", encoding="utf-8") as handle:
    json.dump(trainer_stats.metrics, handle, indent=2)

print(trainer_stats)
print("Adapter saved to:", ADAPTER_DIR)
print("Trainer log history saved to:", RESULTS_DIR / "trainer-log-history.json")
