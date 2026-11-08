import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()
parser.add_argument("--log-history", type=Path, default=Path("results/trainer-log-history.json"))
parser.add_argument("--output-dir", type=Path, default=Path("results"))
parser.add_argument("--show", action="store_true")
args = parser.parse_args()
args.output_dir.mkdir(parents=True, exist_ok=True)

log_history = json.loads(args.log_history.read_text(encoding="utf-8"))
training_by_step = {
    entry["step"]: entry["loss"]
    for entry in log_history
    if "step" in entry and "loss" in entry
}
validation_by_step = {
    entry["step"]: entry["eval_loss"]
    for entry in log_history
    if "step" in entry and "eval_loss" in entry
}
steps = sorted(set(training_by_step) | set(validation_by_step))

with (args.output_dir / "loss-history.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["step", "training_loss", "validation_loss"])
    for step in steps:
        writer.writerow([
            step,
            training_by_step.get(step, ""),
            validation_by_step.get(step, ""),
        ])

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(
    sorted(training_by_step),
    [training_by_step[step] for step in sorted(training_by_step)],
    marker="o",
    linewidth=1.5,
    label="Training loss",
)
ax.plot(
    sorted(validation_by_step),
    [validation_by_step[step] for step in sorted(validation_by_step)],
    marker="s",
    linewidth=2,
    label="Validation loss",
)
ax.set_xlabel("Optimizer step")
ax.set_ylabel("Loss")
ax.set_title("Incident triage QLoRA: training and validation loss")
ax.legend()
ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(args.output_dir / "loss-diagram.png", dpi=160)
if args.show:
    plt.show()
plt.close(fig)

print("Training log entries:", len(training_by_step))
print("Validation log entries:", len(validation_by_step))
print("Saved loss history and diagram to:", args.output_dir)
