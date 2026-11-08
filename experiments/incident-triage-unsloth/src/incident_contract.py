import json

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
TARGET_FIELDS = ["service", "severity", "category", "summary", "next_action", "escalate"]

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
