import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("INCIDENT_TRIAGE_DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

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
