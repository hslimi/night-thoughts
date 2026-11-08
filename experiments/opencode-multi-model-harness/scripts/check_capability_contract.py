#!/usr/bin/env python3
"""Check the fallback capability contract against public model catalogs.

Reads models.dev and the OpenRouter models API. Needs no API key and makes no
model calls. This is a static check of advertised capabilities: it cannot prove
that a route works in practice.

Exit code: 0 if every route and edge passes, 1 otherwise.
"""
import datetime
import json
import sys
import urllib.request

MODELS_DEV = "https://models.dev/api.json"
OPENROUTER = "https://openrouter.ai/api/v1/models"

# Each chain is primary first, then backups in order.
SETUPS = {
    "best": {
        "pdf": "native",
        "open_weights": False,
        "chains": {
            "fast": ["anthropic/claude-haiku-5-5", "openrouter/anthropic/claude-haiku-5.5"],
            "medium": ["anthropic/claude-sonnet-5-5", "openrouter/anthropic/claude-sonnet-5.5"],
            "heavy": ["anthropic/claude-opus-5-5", "openrouter/anthropic/claude-opus-5.5"],
        },
    },
    "cheap": {
        "pdf": "preprocess",
        "open_weights": True,
        # Set with limit.output in config/cheap/opencode.jsonc.
        "output_caps": {"openrouter/z-ai/glm-5.3-flash": 393216},
        "chains": {
            "orchestrator": [
                "openrouter/z-ai/glm-5.3-flash",
                "deepseek/deepseek-flash",
            ],
            "fast": [
                "deepseek/deepseek-flash",
                "openrouter/deepseek/deepseek-v4.1-flash",
            ],
            "medium": [
                "openrouter/qwen/qwen3.6-35b-a3b",
                "deepseek/deepseek-flash",
                "openrouter/z-ai/glm-5.3-flash",
            ],
            "heavy": [
                "openrouter/qwen/qwen3.8-27b",
                "deepseek/deepseek-flash",
                "openrouter/z-ai/glm-5.3-flash",
            ],
        },
    },
}


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "capability-contract-check"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def lookup(catalog, route):
    provider, model = route.split("/", 1)
    return catalog.get(provider, {}).get("models", {}).get(model)


def route_failures(entry, setup):
    failures = []
    inputs = entry.get("modalities", {}).get("input", [])
    if "image" not in inputs:
        failures.append("no image input")
    if not entry.get("tool_call"):
        failures.append("no tool calling")
    if not entry.get("reasoning"):
        failures.append("no reasoning")
    if setup["pdf"] == "native" and "pdf" not in inputs:
        failures.append("no native PDF")
    if setup["open_weights"] and not entry.get("open_weights"):
        failures.append("not open-weight")
    return failures


def main():
    catalog = fetch(MODELS_DEV)
    openrouter = {m["id"]: m for m in fetch(OPENROUTER)["data"]}
    print(f"catalog check date (UTC): {datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d}")
    print(f"sources: {MODELS_DEV} , {OPENROUTER}\n")
    failed = 0

    for name, setup in SETUPS.items():
        print(f"== {name} (PDF policy: {setup['pdf']})")
        print("-- routes")
        routes = sorted({r for chain in setup["chains"].values() for r in chain})
        for route in routes:
            entry = lookup(catalog, route)
            if not entry:
                print(f"FAIL {route}: not in models.dev")
                failed += 1
                continue
            limit = entry.get("limit", {})
            inputs = ",".join(entry.get("modalities", {}).get("input", []))
            problems = route_failures(entry, setup)
            if route.startswith("openrouter/"):
                live = openrouter.get(route.split("/", 1)[1])
                if not live:
                    problems.append("not in OpenRouter API")
                else:
                    live_output = live["top_provider"].get("max_completion_tokens")
                    if live["context_length"] != limit.get("context") or live_output != limit.get("output"):
                        problems.append(f"catalogs disagree: OpenRouter {live['context_length']}/{live_output}")
            status = "FAIL" if problems else "PASS"
            failed += bool(problems)
            print(f"{status} {route}: context={limit.get('context')} output={limit.get('output')} inputs={inputs} "
                  f"tools={entry.get('tool_call')} reasoning={entry.get('reasoning')} "
                  f"open_weights={entry.get('open_weights')}" + (f" :: {'; '.join(problems)}" if problems else ""))

        print("-- primary to backup edges")
        for tier, chain in setup["chains"].items():
            primary = lookup(catalog, chain[0])
            for position, backup_route in enumerate(chain[1:], start=1):
                backup = lookup(catalog, backup_route)
                if not primary or not backup:
                    print(f"FAIL {tier}: {chain[0]} -> {backup_route}: missing from catalog")
                    failed += 1
                    continue
                problems = []
                caps = setup.get("output_caps", {})
                for field in ("context", "output"):
                    have, need = backup["limit"].get(field), primary["limit"].get(field)
                    if field == "output":
                        have = min(have, caps.get(backup_route, have)) if have is not None else None
                        need = min(need, caps.get(chain[0], need)) if need is not None else None
                    if have is None or need is None or have < need:
                        problems.append(f"{field} {have} below primary {need}")
                if setup["pdf"] == "native" and "pdf" not in backup["modalities"]["input"]:
                    problems.append("backup lacks native PDF")
                if position == 1 and chain[0].split("/")[0] == backup_route.split("/")[0]:
                    problems.append("first backup uses the same hosted route")
                status = "FAIL" if problems else "PASS"
                failed += bool(problems)
                print(f"{status} {tier} backup {position}: {chain[0]} -> {backup_route}"
                      + (f" :: {'; '.join(problems)}" if problems else ""))
        print()

    print(f"result: {'FAIL, ' + str(failed) + ' problem(s)' if failed else 'PASS'}")
    print("scope: advertised capabilities only; route independence compares the hosted route, not the upstream.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
