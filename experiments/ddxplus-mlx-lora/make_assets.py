import argparse
import base64
import hashlib
import html
import json
import re
import struct
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
ASSETS = ROOT / "article-assets"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def svg_text(x, y, value, size=20, color="#172033", weight=400, mono=False, anchor="start"):
    family = "Menlo, monospace" if mono else "-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    return (
        f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
        f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{html.escape(str(value))}</text>'
    )


def svg_header(title, subtitle, height):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="{height}" viewBox="0 0 1500 {height}">',
        '<rect width="1500" height="100%" fill="#f4f7fb"/>',
        '<rect x="40" y="32" width="1420" height="100" rx="18" fill="#ffffff"/>',
        '<rect x="40" y="32" width="7" height="100" rx="3" fill="#0f766e"/>',
        svg_text(72, 76, title, 31, "#102a43", 650),
        svg_text(72, 110, subtitle, 18, "#52606d"),
    ]


def svg_footer(source, height):
    lines = textwrap.wrap(f"Source: {source}", width=92) or ["Source unavailable"]
    first_y = height - 27 - 21 * (len(lines) - 1)
    elements = [
        svg_text(60, first_y + 21 * index, line, 15, "#52606d", mono=True)
        for index, line in enumerate(lines)
    ]
    elements += [
        svg_text(1440, height - 27, "Synthetic DDXPlus cases · educational ML experiment only", 15, "#52606d", anchor="end"),
        "</svg>",
    ]
    return elements


def write_svg(name, elements):
    ASSETS.mkdir(exist_ok=True)
    path = ASSETS / f"{name}.svg"
    path.write_text("\n".join(elements) + "\n")
    print(f"Wrote article-assets/{name}.svg")


def read_training_losses():
    log_path = RESULTS / "logs" / "part4-train-full.log"
    train = []
    validation = []
    for line in log_path.read_text().splitlines():
        line = ANSI.sub("", line)
        match = re.match(r"^\s*(\d+)\s+val\s+(\d+(?:\.\d+)?)\s+", line)
        if match:
            validation.append((int(match.group(1)), float(match.group(2))))
            continue
        match = re.match(r"^\s*(\d+)\s+(\d+(?:\.\d+)?)\s+[▲▼]\s+\d+\s+", line)
        if match:
            train.append((int(match.group(1)), float(match.group(2))))
    config = json.loads((RESULTS / "training-config.json").read_text())
    assert len(train) == config["iters"] // config["steps_per_report"]
    assert len(validation) == config["iters"] // config["steps_per_eval"] + 1
    assert train[-1][0] == validation[-1][0] == config["iters"]
    assert [point[0] for point in train] == list(range(10, 1201, 10))
    assert [point[0] for point in validation] == [1, 200, 400, 600, 800, 1000, 1200]
    result = {
        "source": "results/logs/part4-train-full.log",
        "training_losses": [{"iteration": i, "loss": loss} for i, loss in train],
        "validation_losses": [{"iteration": i, "loss": loss} for i, loss in validation],
        "first_reported_training_iteration": train[0][0],
        "note": "Iteration 1 is a validation measurement, not a reported training loss.",
    }
    (RESULTS / "training-losses.json").write_text(json.dumps(result, indent=2) + "\n")
    return train, validation


def loss_plot(train, validation, x, y, width, height, maximum, start=1):
    train = [(i, loss) for i, loss in train if i >= start]
    validation = [(i, loss) for i, loss in validation if i >= start]
    ticks = [0, 300, 600, 900, 1200] if start == 1 else [100, 400, 800, 1200]
    y_ticks = [0, maximum / 4, maximum / 2, maximum * 3 / 4, maximum]
    elements = []
    for tick in y_ticks:
        py = y + height - height * tick / maximum
        elements.append(f'<line x1="{x}" y1="{py:.2f}" x2="{x + width}" y2="{py:.2f}" stroke="#d9e2ec"/>')
        elements.append(svg_text(x - 12, py + 5, f"{tick:.2f}", 15, "#627d98", anchor="end"))
    for tick in ticks:
        px = x + width * (tick - start) / (1200 - start)
        elements.append(svg_text(px, y + height + 28, tick, 15, "#627d98", anchor="middle"))
    def points(records):
        return " ".join(
            f"{x + width * (i - start) / (1200 - start):.2f},{y + height - height * loss / maximum:.2f}"
            for i, loss in records
        )
    elements.append(f'<polyline points="{points(train)}" fill="none" stroke="#0f766e" stroke-width="3" stroke-linejoin="round"/>')
    elements.append(f'<polyline points="{points(validation)}" fill="none" stroke="#c2410c" stroke-width="3" stroke-linejoin="round"/>')
    for i, loss in validation:
        px = x + width * (i - start) / (1200 - start)
        py = y + height - height * loss / maximum
        elements.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="5" fill="#c2410c"/>')
    return elements


def make_loss_asset():
    train, validation = read_training_losses()
    elements = svg_header(
        "Training and validation loss",
        "Qwen2.5-1.5B-Instruct-4bit · LoRA · 1,200 iterations · prompt masking enabled",
        1030,
    )
    elements += [
        '<rect x="40" y="150" width="1420" height="442" rx="18" fill="#ffffff"/>',
        svg_text(72, 190, "Full training run", 21, "#102a43", 600),
        '<line x1="1110" y1="181" x2="1142" y2="181" stroke="#0f766e" stroke-width="4"/>',
        svg_text(1152, 187, "Training", 16, "#334e68"),
        '<line x1="1260" y1="181" x2="1292" y2="181" stroke="#c2410c" stroke-width="4"/>',
        svg_text(1302, 187, "Validation", 16, "#334e68"),
    ]
    elements += loss_plot(train, validation, 145, 224, 1230, 300, 2.4)
    elements += [
        '<rect x="40" y="610" width="920" height="353" rx="18" fill="#ffffff"/>',
        svg_text(72, 649, "Iterations 100–1,200 · expanded loss scale", 20, "#102a43", 600),
    ]
    elements += loss_plot(train, validation, 130, 684, 750, 210, 0.2, start=100)
    elements += [
        '<rect x="980" y="610" width="480" height="353" rx="18" fill="#ffffff"/>',
        svg_text(1010, 654, "Reported checkpoints", 21, "#102a43", 600),
        svg_text(1010, 700, "First training report · iter 10", 17, "#52606d"),
        svg_text(1010, 738, f"{train[0][1]:.3f}", 32, "#0f766e", 650),
        svg_text(1010, 790, "Final training loss · iter 1,200", 17, "#52606d"),
        svg_text(1010, 828, f"{train[-1][1]:.3f}", 32, "#0f766e", 650),
        svg_text(1010, 880, "Final validation loss · iter 1,200", 17, "#52606d"),
        svg_text(1010, 918, f"{validation[-1][1]:.3f}", 32, "#c2410c", 650),
    ]
    elements += svg_footer("results/logs/part4-train-full.log → results/training-losses.json", 1030)
    write_svg("01-training-loss", elements)


METRICS = [
    ("Top-1 accuracy", "top1_accuracy", True),
    ("Top-3 accuracy", "top3_accuracy", True),
    ("Structured-response rate", "structured_response_rate", True),
    ("Mean reference overlap@3", "mean_reference_overlap_at_3", False),
]


def load_summary(name):
    summary = json.loads((RESULTS / f"{name}.summary.json").read_text())
    qualitative = json.loads((RESULTS / "qualitative-examples.json").read_text())
    assert summary["cases"] == 490
    assert summary["test_cases_sha256"] == qualitative["test_cases_sha256"]
    assert summary["generation"] == {"max_tokens": 220, "temperature": 0.0}
    return summary


def metric_value(summary, key, percentage):
    return f"{summary[key]:.2%}" if percentage else f"{summary[key]:.3f} / 3"


def make_summary_asset(mode, filename, title, subtitle):
    summary = load_summary(mode)
    elements = svg_header(title, subtitle, 820)
    elements += [
        '<rect x="40" y="150" width="1420" height="105" rx="18" fill="#e6f6f2"/>',
        svg_text(72, 190, "COMPLETE HELD-OUT EVALUATION", 16, "#0f766e", 650),
        svg_text(72, 231, f"{summary['cases']} cases", 31, "#102a43", 650),
        svg_text(1420, 210, "Greedy generation · max_tokens 220", 20, "#334e68", anchor="end"),
        svg_text(1420, 238, "Identical test file and settings across modes", 16, "#52606d", anchor="end"),
        '<rect x="40" y="275" width="1420" height="450" rx="18" fill="#ffffff"/>',
        svg_text(75, 319, "METRIC", 16, "#627d98", 600),
        svg_text(1420, 319, "OBSERVED RESULT", 16, "#627d98", 600, anchor="end"),
    ]
    for index, (label, key, percentage) in enumerate(METRICS):
        y = 390 + 82 * index
        if index:
            elements.append(f'<line x1="75" y1="{y - 44}" x2="1425" y2="{y - 44}" stroke="#e6edf3"/>')
        elements += [
            svg_text(75, y, label, 23, "#334e68"),
            svg_text(1420, y, metric_value(summary, key, percentage), 31, "#0f766e", 650, anchor="end"),
        ]
    elements += svg_footer(f"results/{mode}.summary.json", 820)
    write_svg(filename, elements)


def make_fused_asset():
    adapter = load_summary("adapter")
    failed = load_summary("fused")
    fused = load_summary("fused-dequantized-full")
    comparison = json.loads((RESULTS / "fused-dequantized-full-comparison.json").read_text())
    review = json.loads((RESULTS / "fused-dequantized-full-deployment-review.json").read_text())
    differences = json.loads((ROOT / review["response_differences"]).read_text())
    assert review["status"] == "reviewed_with_differences"
    assert review["deployment_eligible"] is True
    assert review["strict_identity_gate_passed"] is False
    assert review["model_path"] == "fused/ddxplus-qwen-dequantized"
    assert comparison["test_cases_sha256"] == review["test_cases_sha256"] == fused["test_cases_sha256"]
    assert len(differences) == comparison["response_or_prediction_mismatches"]
    assert comparison["exact_response_matches"] + len(differences) == 490
    elements = svg_header(
        "Fused-model verification",
        "The quantized artifact failed; a separate dequantized artifact was independently evaluated",
        990,
    )
    elements += [
        '<rect x="40" y="150" width="1420" height="113" rx="18" fill="#fff4e6"/>',
        svg_text(72, 190, "ADAPTER ↔ DEQUANTIZED FUSED", 16, "#0f766e", 650),
        svg_text(72, 234, f"{comparison['exact_response_matches']} / 490 exact responses · {len(differences)} differences", 29, "#102a43", 650),
        svg_text(1420, 207, f"{comparison['most_likely_matches']} / 490 same top-1 label", 19, "#334e68", anchor="end"),
        svg_text(1420, 240, "Strict response identity: FAILED", 17, "#9a3412", 600, anchor="end"),
        '<rect x="40" y="285" width="1420" height="445" rx="18" fill="#ffffff"/>',
        svg_text(75, 327, "METRIC", 15, "#627d98", 600),
        svg_text(560, 327, "ADAPTER", 15, "#627d98", 600, anchor="middle"),
        svg_text(930, 327, "QUANTIZED · FAILED", 15, "#9a3412", 600, anchor="middle"),
        svg_text(1330, 327, "DEQUANTIZED", 15, "#0f766e", 600, anchor="middle"),
    ]
    for index, (label, key, percentage) in enumerate(METRICS):
        y = 400 + 82 * index
        if index:
            elements.append(f'<line x1="75" y1="{y - 44}" x2="1425" y2="{y - 44}" stroke="#e6edf3"/>')
        elements += [
            svg_text(75, y, label, 20, "#334e68"),
            svg_text(560, y, metric_value(adapter, key, percentage), 24, "#102a43", 600, anchor="middle"),
            svg_text(930, y, metric_value(failed, key, percentage), 24, "#9a3412", 600, anchor="middle"),
            svg_text(1330, y, metric_value(fused, key, percentage), 24, "#0f766e", 650, anchor="middle"),
        ]
    elements += [
        '<rect x="40" y="750" width="1420" height="164" rx="18" fill="#ffffff"/>',
        svg_text(72, 792, "Correction: mlx_lm.fuse --dequantize", 22, "#102a43", 600),
        svg_text(72, 830, f"Strict identity failed: {len(differences)} changed responses; deployment review allows at most 2%.", 20, "#9a3412"),
        svg_text(72, 867, "The quantized artifact was rejected. No adapter retraining was performed.", 20, "#52606d"),
        svg_text(72, 895, "Reviewed differences are not exact equivalence or clinical validation.", 17, "#9a3412"),
    ]
    elements += svg_footer("results/fused-dequantized-full-comparison.json · results/fused-dequantized-full-deployment-review.json", 990)
    write_svg("04-fused-verification", elements)


def response_panel(x, y, width, height, title, response, color):
    elements = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="18" fill="#ffffff"/>',
        f'<rect x="{x}" y="{y}" width="{width}" height="6" rx="3" fill="{color}"/>',
        svg_text(x + 28, y + 47, title, 22, "#102a43", 650),
    ]
    lines = []
    for line in response.splitlines():
        lines.extend(textwrap.wrap(line, width=60) if line else [""])
    assert y + 85 + len(lines) * 25 <= y + height - 15
    for index, line in enumerate(lines):
        elements.append(svg_text(x + 28, y + 88 + index * 25, line, 17, "#334e68", mono=True))
    return elements


def qualitative_examples():
    examples = json.loads((RESULTS / "qualitative-examples.json").read_text())["examples"]
    return examples


def make_dataset_asset():
    import ast

    import pandas as pd

    from prepare_ddxplus import make_case_prompt

    cases = [
        json.loads(line)
        for line in (ROOT / "evaluation" / "test_cases.jsonl").read_text().splitlines()
    ]
    case = next(case for case in cases if case["case_id"] == "test-0000")
    source_index = case["source_index"]
    row = pd.read_csv(
        ROOT / "raw" / "release_test_patients",
        skiprows=range(1, source_index + 1),
        nrows=1,
    ).iloc[0]
    assert row["PATHOLOGY"] == case["ground_truth"]
    assert row["INITIAL_EVIDENCE"] == case["initial_evidence"]
    assert isinstance(ast.literal_eval(row["EVIDENCES"]), list)
    assert isinstance(ast.literal_eval(row["DIFFERENTIAL_DIAGNOSIS"]), list)
    assert make_case_prompt(row) == case["prompt"]
    raw_record = (
        f"AGE: {row['AGE']}\n"
        f"SEX: {row['SEX']}\n\n"
        f"PATHOLOGY:\n{row['PATHOLOGY']}\n\n"
        f"INITIAL_EVIDENCE:\n{row['INITIAL_EVIDENCE']}\n\n"
        f"EVIDENCES (CSV list field):\n{row['EVIDENCES']}\n\n"
        f"DIFFERENTIAL_DIAGNOSIS (CSV list field):\n{row['DIFFERENTIAL_DIAGNOSIS']}"
    )
    line_count = max(
        sum(len(textwrap.wrap(line, width=60)) if line else 1 for line in text.splitlines())
        for text in (raw_record, case["prompt"])
    )
    panel_height = max(750, 115 + line_count * 25)
    height = panel_height + 410
    elements = svg_header(
        "From coded evidence to a patient prompt",
        f"{case['case_id']} · one genuine synthetic official row · source-derived evidence figure",
        height,
    )
    elements += [
        '<rect x="40" y="150" width="1420" height="118" rx="18" fill="#e6f6f2"/>',
        svg_text(72, 192, "EXTENSIONLESS CSV MEMBER · release_test_patients", 16, "#0f766e", 650),
        svg_text(72, 230, f"Official data-row index: {source_index} · decoded prompt matches the saved held-out case", 20, "#334e68"),
        svg_text(72, 257, "CSV lists use ast.literal_eval. No evidence or ground-truth label was added for this figure.", 16, "#52606d"),
    ]
    elements += response_panel(40, 295, 690, panel_height, "Official coded record · selected CSV fields", raw_record, "#9a3412")
    elements += response_panel(770, 295, 690, panel_height, "Decoded user prompt", case["prompt"], "#0f766e")
    elements += svg_footer("raw/release_test_patients → evaluation/test_cases.jsonl · test-0000", height)
    write_svg("00-ddxplus-decoding", elements)


def make_improved_asset():
    example = qualitative_examples()["improved"]
    assert not example["base"]["top1"] and example["adapter"]["top1"]
    elements = svg_header(
        "An improved held-out prediction",
        f"{example['case_id']} · DDXPlus label: {example['ground_truth']} · greedy generation",
        1070,
    )
    elements += [
        '<rect x="40" y="150" width="1420" height="82" rx="18" fill="#e6f6f2"/>',
        svg_text(72, 185, "Same synthetic patient case and system prompt", 20, "#334e68"),
        svg_text(72, 215, "The adapter’s top-1 prediction now matches the dataset label.", 19, "#0f766e", 600),
    ]
    elements += response_panel(40, 255, 690, 710, "Base · incorrect", example["base"]["response"], "#9a3412")
    elements += response_panel(770, 255, 690, 710, "Adapter · matches label", example["adapter"]["response"], "#0f766e")
    elements += svg_footer("results/qualitative-examples.json → examples.improved", 1070)
    write_svg("05-improved-held-out-example", elements)


def make_failure_asset():
    example = qualitative_examples()["well_formatted_incorrect"]
    shared = qualitative_examples()["shared_failure"]
    assert example["adapter"]["structured"] and not example["adapter"]["top1"]
    assert not shared["base"]["top1"] and not shared["adapter"]["top1"]
    elements = svg_header(
        "Well-formatted does not mean correct",
        f"A genuine remaining failure · {example['case_id']} · structured response, incorrect top-1 label",
        1110,
    )
    elements += [
        '<rect x="40" y="150" width="690" height="125" rx="18" fill="#ffffff"/>',
        '<rect x="770" y="150" width="690" height="125" rx="18" fill="#fff4e6"/>',
        svg_text(72, 190, "DDXPLUS LABEL", 16, "#627d98", 650),
        svg_text(72, 237, example["ground_truth"], 31, "#102a43", 650),
        svg_text(802, 190, "ADAPTER TOP-1 PREDICTION", 16, "#9a3412", 650),
        svg_text(802, 237, example["adapter"]["most_likely"], 31, "#9a3412", 650),
    ]
    elements += response_panel(40, 300, 1420, 615, "Adapter response · fluent format, wrong top-1 prediction", example["adapter"]["response"], "#9a3412")
    elements += [
        '<rect x="40" y="940" width="1420" height="96" rx="18" fill="#ffffff"/>',
        svg_text(72, 980, f"Shared failure {shared['case_id']} · dataset label: {shared['ground_truth']}", 20, "#334e68", 600),
        svg_text(72, 1016, f"Base: {shared['base']['most_likely']}  ·  Adapter: {shared['adapter']['most_likely']}", 20, "#9a3412"),
    ]
    elements += svg_footer("results/qualitative-examples.json → examples.well_formatted_incorrect + shared_failure", 1110)
    write_svg("06-remaining-failure", elements)


def make_ablation_asset():
    probe = json.loads((RESULTS / "counterfactual.json").read_text())
    assert probe["removed_section"] == "Symptoms"
    assert probe["ground_truth_after_edit"] is None
    assert not probe["edited_case_has_validated_ground_truth"]
    assert probe["original_matches_adapter_evaluation"]
    removed_bullet = f"- {probe['removed_finding']}"
    assert removed_bullet in probe["original_prompt"]
    assert removed_bullet not in probe["changed_prompt"]
    evidences = json.loads((ROOT / "raw" / "release_evidences.json").read_text())
    initial_question = evidences[probe["initial_evidence"]]["question_en"]
    assert f"- {initial_question}" in probe["original_prompt"]
    assert f"- {initial_question}" in probe["changed_prompt"]
    response_change = "unchanged" if probe["responses"]["original"] == probe["responses"]["one_finding_removed"] else "changed"
    elements = svg_header(
        f"Evidence ablation: a genuine {response_change} response",
        f"{probe['case_id']} · adapter · greedy generation · one non-initial finding removed",
        1060,
    )
    elements += [
        '<rect x="40" y="150" width="1420" height="205" rx="18" fill="#fff4e6"/>',
        svg_text(72, 191, "REMOVED FROM THE SYMPTOMS SECTION", 16, "#9a3412", 650),
    ]
    for index, line in enumerate(textwrap.wrap(probe["removed_finding"], width=105)):
        elements.append(svg_text(72, 232 + index * 27, line, 21, "#102a43"))
    elements += [
        svg_text(72, 302, f"Initial evidence preserved: {initial_question} Yes.", 18, "#0f766e"),
        svg_text(72, 336, "The original dataset label is not assigned to the edited case; no new ground truth is inferred.", 18, "#9a3412"),
    ]
    original = probe["responses"]["original"]
    changed = probe["responses"]["one_finding_removed"]
    elements += response_panel(40, 380, 690, 535, "Original evidence", original, "#0f766e")
    elements += response_panel(770, 380, 690, 535, "One finding removed", changed, "#9a3412")
    elements += [
        svg_text(72, 951, "Observed result: the two responses are identical." if original == changed else "Observed result: the response changed after ablation.", 22, "#9a3412", 650),
        svg_text(72, 985, "This probe measures sensitivity to evidence removal, not clinical correctness.", 18, "#52606d"),
    ]
    elements += svg_footer("results/counterfactual.json · results/logs/part5-ablation-verification.log", 1060)
    write_svg("07-evidence-ablation", elements)


def make_omlx_asset():
    verification = json.loads((RESULTS / "omlx-verification.json").read_text())
    selected = json.loads((RESULTS / "omlx-selected-model.json").read_text())
    qualitative = json.loads((RESULTS / "qualitative-examples.json").read_text())
    assert verification["model"] == selected["display_id"] == "ddxplus-qwen"
    assert verification["response_model_matches_discovery"]
    assert verification["response_model_matches_discovery"]
    assert verification["test_cases_sha256"] == qualitative["test_cases_sha256"]
    assert verification["max_tokens"] == 220
    elements = svg_header(
        "oMLX discovery and held-out generation",
        "Verified through the actual system daemon · separate dequantized fused artifact",
        900,
    )
    elements += [
        '<rect x="40" y="150" width="1420" height="132" rx="18" fill="#e6f6f2"/>',
        svg_text(72, 193, "MODEL ID DISCOVERED THROUGH /v1/models", 16, "#0f766e", 650),
        svg_text(72, 239, verification["model"], 29, "#102a43", 650),
        svg_text(1420, 193, f"Held-out case: {verification['case_id']}", 20, "#334e68", anchor="end"),
        svg_text(1420, 232, "Response model matches discovered ID", 18, "#0f766e", anchor="end"),
        svg_text(1420, 260, "Source-derived evidence figure, not a terminal capture", 15, "#52606d", anchor="end"),
    ]
    elements += response_panel(40, 305, 1420, 510, f"Actual oMLX response · {verification['case_id']}", verification["response"], "#0f766e")
    elements += [
        svg_text(72, 855, "Greedy generation · max_tokens 220 · credentials omitted", 19, "#52606d"),
    ]
    elements += svg_footer("results/omlx-verification.json · results/logs/part7-omlx-resumed.log", 900)
    write_svg("08-omlx-verification", elements)


def png_image(path, x, y, width, height):
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    actual_width, actual_height = struct.unpack(">II", data[16:24])
    encoded = base64.b64encode(data).decode("ascii")
    return (
        f'<svg x="{x}" y="{y}" width="{width}" height="{height}" '
        f'viewBox="0 0 {actual_width} {actual_height}">'
        f'<image width="{actual_width}" height="{actual_height}" '
        f'href="data:image/png;base64,{encoded}"/></svg>'
    )


def make_qwenpaw_asset():
    verification = json.loads((RESULTS / "qwenpaw-console-verification.json").read_text())
    direct = json.loads((RESULTS / "omlx-verification.json").read_text())
    selected = json.loads((RESULTS / "omlx-selected-model.json").read_text())
    metadata = json.loads((ROOT / "evaluation" / "metadata.json").read_text())
    cases = [
        json.loads(line)
        for line in (ROOT / "evaluation" / "test_cases.jsonl").read_text().splitlines()
    ]
    case = next(case for case in cases if case["case_id"] == verification["case_id"])
    from evaluate import parse_response

    parsed = parse_response(verification["response"], metadata["conditions"])
    console_top1 = parsed["most_likely"] or "No closed-set label parsed"
    top1_matches = console_top1 == case["ground_truth"]
    message = (RESULTS / "qwenpaw-console-message.txt").read_bytes()
    assert hashlib.sha256(message).hexdigest() == verification["prompt_sha256"]
    assert message.decode() == metadata["system_prompt"] + "\n\n" + case["prompt"]
    assert verification["round_trip_succeeded"] is True
    assert verification["matches_dataset_label"] is top1_matches
    assert verification["matches_direct_omlx_response"] is False
    assert verification["evaluation_metric"] is False
    assert verification["dataset_ground_truth"] == case["ground_truth"] == direct["ground_truth"]
    assert verification["case_id"] == direct["case_id"]
    assert verification["response"] != direct["response"]
    assert verification["selected_model"]["model"] == selected["model_id"]
    assert direct["model"] == selected["display_id"]
    capture = verification["capture"]
    elements = svg_header(
        "QwenPaw: a real fused-model chat",
        f"{case['case_id']} · console transport verified · the response differs from direct oMLX",
        1220,
    )
    elements += [
        '<rect x="40" y="150" width="1420" height="120" rx="18" fill="#fff4e6"/>',
        svg_text(72, 193, f"DDXPlus label: {case['ground_truth']}", 23, "#102a43", 600),
        svg_text(72, 235, f"Console top-1: {console_top1} · {'matches label' if top1_matches else 'incorrect'}", 23, "#9a3412" if not top1_matches else "#0f766e", 600),
        svg_text(1420, 193, "Real chat round trip: PASSED", 20, "#0f766e", 600, anchor="end"),
        svg_text(1420, 232, "Not a benchmark or direct-equivalence result", 17, "#52606d", anchor="end"),
        '<rect x="40" y="290" width="1420" height="630" rx="18" fill="#171717"/>',
        png_image(ROOT / capture["response_crop"], 70, 320, 1360, 565),
        '<rect x="40" y="940" width="1420" height="180" rx="18" fill="#ffffff"/>',
        svg_text(72, 978, "Per-chat model selector · same capture", 18, "#334e68", 600),
        png_image(ROOT / capture["model_selection_crop"], 72, 997, 673, 95),
        svg_text(810, 1005, "QwenPaw agent context and its existing settings apply.", 18, "#334e68"),
        svg_text(810, 1042, "The global model selection was not changed.", 18, "#334e68"),
        svg_text(810, 1079, "The repaired oMLX credential is not shown.", 18, "#334e68"),
        svg_text(72, 1160, "Two unmodified UI crops; account, history, workspace controls, and desktop content excluded.", 17, "#52606d"),
    ]
    elements += svg_footer("results/qwenpaw-console-verification.json · genuine QwenPaw console crops", 1220)
    write_svg("09-qwenpaw-fused-console", elements)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["dataset", "loss", "evaluation", "fused", "qualitative", "ablation", "omlx", "qwenpaw"], required=True)
    args = parser.parse_args()
    if args.stage == "dataset":
        make_dataset_asset()
    elif args.stage == "loss":
        make_loss_asset()
    elif args.stage == "evaluation":
        make_summary_asset("base", "02-base-evaluation", "Base-model evaluation", "Qwen2.5-1.5B-Instruct-4bit · before adapter training")
        make_summary_asset("adapter", "03-adapter-evaluation", "Adapter evaluation", "Qwen2.5-1.5B-Instruct-4bit + trained LoRA adapter")
    elif args.stage == "fused":
        make_fused_asset()
    elif args.stage == "qualitative":
        make_improved_asset()
        make_failure_asset()
    elif args.stage == "ablation":
        make_ablation_asset()
    elif args.stage == "omlx":
        make_omlx_asset()
    else:
        make_qwenpaw_asset()


if __name__ == "__main__":
    main()
