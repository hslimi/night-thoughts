import argparse
import hashlib
import json
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
BASE_URL = "http://127.0.0.1:8088"
STATE_PATH = RESULTS / "qwenpaw-original-selection.json"
MODEL_STATE_FIELDS = (
    "models",
    "extra_models",
    "discovered_models",
    "hidden_model_ids",
    "removed_model_ids",
)
CONNECTION_FIELDS = (
    "base_url",
    "enabled",
    "chat_model",
    "require_api_key",
    "freeze_url",
    "is_custom",
)


def write_json(path, value, sensitive=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    if sensitive:
        path.chmod(0o600)


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def api_request(path, method="GET", payload=None):
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        method=method,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def active_model(agent_id, scope):
    query = urllib.parse.urlencode({"scope": scope, "agent_id": agent_id})
    return api_request(f"/api/models/active?{query}")["active_llm"]


def omlx_provider():
    return next(
        provider for provider in api_request("/api/models")
        if provider["id"] == "omlx"
    )


def model_state(provider=None):
    provider = provider or omlx_provider()
    discovery_metadata = {"capability_provenance", "discovered_at", "released_at"}
    state = {}
    for field in MODEL_STATE_FIELDS:
        value = provider.get(field, [])
        if field in {"models", "extra_models", "discovered_models"}:
            value = [
                {
                    key: item
                    for key, item in model.items()
                    if key not in discovery_metadata
                }
                for model in value
            ]
        state[field] = value
    return state


def sanitized_base_url(value):
    parsed = urllib.parse.urlsplit(value)
    if parsed.query or parsed.fragment:
        raise ValueError("Refusing to save a provider URL containing a query or fragment")
    host = parsed.hostname or ""
    if ":" in host:
        host = f"[{host}]"
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    return urllib.parse.urlunsplit((parsed.scheme, host, parsed.path, "", ""))


def connection_settings():
    settings = {}
    for provider in api_request("/api/models"):
        selected = {
            key: provider[key]
            for key in CONNECTION_FIELDS
            if key in provider
        }
        if "base_url" in selected:
            selected["base_url"] = sanitized_base_url(selected["base_url"])
        selected["api_key_configured"] = bool(provider.get("api_key"))
        settings[provider["id"]] = selected
    return settings


def set_active_model(agent_id, selection):
    selected = api_request(
        "/api/models/active",
        "PUT",
        {
            **selection,
            "scope": "agent",
            "agent_id": agent_id,
        },
    )["active_llm"]
    if selected != selection:
        raise RuntimeError("QwenPaw returned a different model selection")
    return selected


def agent_config_path(agent_id):
    config_path = Path.home() / ".qwenpaw" / "config.json"
    config = json.loads(config_path.read_text())
    workspace = config["agents"]["profiles"][agent_id]["workspace_dir"]
    agent_path = Path(workspace).expanduser() / "agent.json"
    secret_root = (Path.home() / ".qwenpaw.secret").resolve()
    for path in (config_path, agent_path):
        if path.resolve().is_relative_to(secret_root):
            raise ValueError("Refusing to access QwenPaw's credential store")
    return config_path, agent_path


def checkpoint(stage, artifact):
    write_json(
        RESULTS / "checkpoints" / f"{stage}.json",
        {
            "stage": stage,
            "status": "complete",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "artifact": artifact,
        },
    )


def configuration_backups(state):
    config_path, agent_path = agent_config_path(state["agent_id"])
    return [
        (
            config_path,
            config_path.with_name(state["configuration_backup"]),
            state["configuration_mode"],
            state["configuration_sha256"],
        ),
        (
            agent_path,
            agent_path.with_name(state["agent_backup"]),
            state["agent_mode"],
            state["agent_sha256"],
        ),
    ]


def restore_configuration(state):
    for destination, backup, mode, expected_hash in configuration_backups(state):
        if not backup.is_file():
            raise FileNotFoundError(f"Missing rollback backup: {backup.name}")
        if file_sha256(backup) != expected_hash:
            raise ValueError(f"Rollback backup differs from its saved hash: {backup.name}")
        shutil.copyfile(backup, destination)
        destination.chmod(mode)
        if file_sha256(destination) != expected_hash:
            raise RuntimeError(f"Configuration restore did not verify: {destination.name}")


def restore_provider_registration(state):
    if not state["added_model_to_qwenpaw"]:
        return
    model_id = state["experiment_model_id"]
    registered = {
        model["id"]
        for field in ("models", "extra_models", "discovered_models")
        for model in omlx_provider().get(field, [])
    }
    if model_id in registered:
        encoded_id = urllib.parse.quote(model_id, safe="")
        api_request(f"/api/models/omlx/models/{encoded_id}", "DELETE")
    python = Path.home() / ".qwenpaw" / "venv" / "bin" / "python"
    command = [
        str(python),
        str(ROOT / "qwenpaw_provider_state.py"),
        "--removed-model-ids",
        json.dumps(state["original_provider_state"]["removed_model_ids"]),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError(
            "The installed QwenPaw provider API could not restore the original "
            "removal list. Rollback is not complete."
        ) from error
    print("Restored the original oMLX model-removal list through QwenPaw's provider API.")


def select_model(agent_id, model_id):
    config_path, agent_path = agent_config_path(agent_id)
    if STATE_PATH.exists():
        raise FileExistsError("Saved QwenPaw state exists; inspect it before reselecting")
    if (RESULTS / "checkpoints" / "part8-prepared-rollback.json").exists():
        raise RuntimeError("A prepared rollback must be verified before reselecting")
    original_agent = active_model(agent_id, "agent")
    original_global = active_model(agent_id, "global")
    if not original_agent or not original_agent.get("model"):
        raise ValueError("This helper expects an existing per-agent model to restore")
    provider = omlx_provider()
    if not provider.get("api_key"):
        raise RuntimeError(
            "QwenPaw has no saved oMLX credential. Synchronize it with "
            "qwenpaw_provider_state.py --sync-current-key before selecting a model."
        )
    original_model_ids = {
        model["id"]
        for field in ("models", "extra_models", "discovered_models")
        for model in provider.get(field, [])
    }
    state = {
        "agent_id": agent_id,
        "original_agent_selection": original_agent,
        "original_global_selection": original_global,
        "experiment_model_id": model_id,
        "original_provider_state": model_state(provider),
        "original_connection_settings": connection_settings(),
        "added_model_to_qwenpaw": model_id not in original_model_ids,
        "configuration_backup": config_path.name + ".before-ddxplus",
        "agent_backup": agent_path.name + ".before-ddxplus",
        "configuration_mode": config_path.stat().st_mode & 0o777,
        "agent_mode": agent_path.stat().st_mode & 0o777,
    }
    for destination, backup_name in (
        (config_path, state["configuration_backup"]),
        (agent_path, state["agent_backup"]),
    ):
        backup = destination.with_name(backup_name)
        if backup.exists():
            raise FileExistsError(f"A rollback backup already exists: {backup.name}")
        shutil.copy2(destination, backup)
        backup.chmod(0o600)
        hash_key = "configuration_sha256" if destination == config_path else "agent_sha256"
        state[hash_key] = file_sha256(backup)
    write_json(STATE_PATH, state, sensitive=True)

    try:
        if state["added_model_to_qwenpaw"]:
            api_request(
                "/api/models/omlx/models",
                "POST",
                {"id": model_id, "name": "DDXPlus Qwen (fused)"},
            )
        selection = {"provider_id": "omlx", "model": model_id}
        set_active_model(agent_id, selection)
        if active_model(agent_id, "agent") != selection:
            raise RuntimeError("The agent model selection did not persist")
        if active_model(agent_id, "global") != original_global:
            raise RuntimeError("The global model selection changed unexpectedly")
        if connection_settings() != state["original_connection_settings"]:
            raise RuntimeError("A provider connection setting changed unexpectedly")
    except Exception:
        prepare_rollback(agent_id)
        raise

    write_json(
        RESULTS / "qwenpaw-selection-verification.json",
        {
            "agent_id": agent_id,
            "selected_model": {"provider_id": "omlx", "model": model_id},
            "scope": "default agent only",
            "global_selection_preserved": True,
            "provider_connection_settings_preserved": True,
            "experiment_model_registered": state["added_model_to_qwenpaw"],
        },
    )
    checkpoint("part7-qwenpaw-selection", "results/qwenpaw-selection-verification.json")
    print(f"QwenPaw agent {agent_id} now selects oMLX / {model_id}")
    print("Only the per-agent selection and required model registration were changed.")
    print("Global selection, provider URL, API key, and unrelated settings were preserved.")


def prepare_rollback(agent_id):
    state = json.loads(STATE_PATH.read_text())
    if state["agent_id"] != agent_id:
        raise ValueError("The saved state belongs to a different agent")
    prepared = RESULTS / "checkpoints" / "part8-prepared-rollback.json"
    if prepared.exists():
        raise FileExistsError("Rollback is already prepared; restart and verify it")
    config_path, _ = agent_config_path(agent_id)
    if file_sha256(config_path) != state["configuration_sha256"]:
        raise RuntimeError("The global QwenPaw configuration changed; refusing to overwrite it")
    original = state["original_agent_selection"]
    current = active_model(agent_id, "agent")
    if current not in (original, {"provider_id": "omlx", "model": state["experiment_model_id"]}):
        raise RuntimeError("The agent selection changed independently; refusing to overwrite it")
    restore_provider_registration(state)
    restore_configuration(state)
    write_json(
        RESULTS / "qwenpaw-rollback-preparation.json",
        {
            "agent_id": agent_id,
            "configuration_backups_restored": True,
            "model_selection_restored_from_backup": True,
            "original_model_removal_list_restored": state["added_model_to_qwenpaw"],
            "restart_required": True,
            "restart_command": "sudo launchctl kickstart -k system/com.qwenpaw.app",
            "verification_command": "python qwenpaw_model.py --verify-rollback",
        },
    )
    checkpoint("part8-prepared-rollback", "results/qwenpaw-rollback-preparation.json")
    print("Configuration backups and provider model state restored; daemon restart is still required.")
    print("Run: sudo launchctl kickstart -k system/com.qwenpaw.app")
    print("Then run: python qwenpaw_model.py --verify-rollback")


def restart_daemon():
    result = subprocess.run(
        ["sudo", "-n", "launchctl", "kickstart", "-k", "system/com.qwenpaw.app"],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(
            "The actual QwenPaw daemon could not be restarted without local sudo "
            "authorization. Run the printed restart command, then --verify-rollback."
        )


def provider_state_command(argument):
    python = Path.home() / ".qwenpaw" / "venv" / "bin" / "python"
    subprocess.run(
        [str(python), str(ROOT / "qwenpaw_provider_state.py"), argument],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )


def expected_connection_settings(state, permanent_sync):
    expected = json.loads(json.dumps(state["original_connection_settings"]))
    if permanent_sync:
        if "omlx" not in expected:
            raise ValueError("The saved state has no oMLX connection settings")
        expected["omlx"]["api_key_configured"] = True
    return expected


def verify_daemon_restart():
    prepared = json.loads(
        (RESULTS / "checkpoints" / "part8-prepared-rollback.json").read_text()
    )
    prepared_at = datetime.fromisoformat(prepared["completed_at"]).timestamp()
    daemon = subprocess.run(
        ["launchctl", "print", "system/com.qwenpaw.app"],
        capture_output=True,
        text=True,
    )
    pid_line = next(
        (line.strip() for line in daemon.stdout.splitlines() if line.strip().startswith("pid = ")),
        None,
    )
    if daemon.returncode or pid_line is None:
        raise RuntimeError("The actual QwenPaw system daemon is not running")
    process = subprocess.run(
        ["ps", "-p", pid_line.split("=", 1)[1].strip(), "-o", "lstart="],
        check=True,
        capture_output=True,
        text=True,
    )
    started_at = datetime.strptime(
        process.stdout.strip(),
        "%a %b %d %H:%M:%S %Y",
    ).timestamp()
    if started_at + 1 < prepared_at:
        raise RuntimeError(
            "QwenPaw has not restarted since rollback preparation. Run: "
            "sudo launchctl kickstart -k system/com.qwenpaw.app"
        )


def verify_rollback(agent_id):
    state = json.loads(STATE_PATH.read_text())
    if state["agent_id"] != agent_id:
        raise ValueError("The saved state belongs to a different agent")
    if not (RESULTS / "checkpoints" / "part8-prepared-rollback.json").exists():
        raise RuntimeError("Prepare rollback and restart the daemon before verification")
    for destination, _, _, expected_hash in configuration_backups(state):
        if file_sha256(destination) != expected_hash:
            raise RuntimeError(f"Restored configuration differs from backup: {destination.name}")
    sync_path = RESULTS / "qwenpaw-credential-sync.json"
    credential_sync = json.loads(sync_path.read_text()) if sync_path.exists() else {}
    permanent_sync = credential_sync.get("status") == "synchronized_permanently"
    if credential_sync and (
        not permanent_sync
        or credential_sync.get("restore_original_credential_during_rollback") is not False
        or credential_sync.get("persistent_credential_matches_current_omlx") is not True
        or credential_sync.get("credential_values_recorded") is not False
    ):
        raise RuntimeError("The saved QwenPaw credential state is not a verified permanent sync")
    verify_daemon_restart()
    expected_connections = expected_connection_settings(state, permanent_sync)
    original = state["original_agent_selection"]
    deadline = time.monotonic() + 120
    while True:
        try:
            restored = (
                active_model(agent_id, "agent") == original
                and active_model(agent_id, "effective") == original
                and active_model(agent_id, "global") == state["original_global_selection"]
                and model_state() == model_state(state["original_provider_state"])
                and connection_settings() == expected_connections
            )
            if restored:
                if permanent_sync:
                    provider_state_command("--verify-current-key")
                break
        except (OSError, ValueError, KeyError):
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError("QwenPaw did not return to its expected post-rollback state")
        time.sleep(2)
    result = {
        "agent_id": agent_id,
        "restored_agent_selection": original,
        "global_selection_preserved": True,
        "provider_connection_settings_preserved": True,
        "non_credential_connection_settings_preserved": True,
        "provider_model_metadata_and_removal_list_restored": True,
        "discovery_metadata_fields_excluded": [
            "capability_provenance",
            "discovered_at",
            "released_at",
        ],
        "discovery_metadata_may_refresh": True,
        "experiment_model_registration_removed": state["added_model_to_qwenpaw"],
        "configuration_backup_restored_exactly": True,
        "agent_backup_restored_exactly": True,
        "actual_system_daemon_restarted_after_preparation": True,
        "permanent_omlx_credential_sync_retained": permanent_sync,
        "original_omlx_credential_restored": False if permanent_sync else None,
        "direct_credential_store_file_backup_performed": False,
        "adapter_and_fused_model_retained": True,
    }
    write_json(RESULTS / "qwenpaw-rollback.json", result, sensitive=True)
    checkpoint("part8-rollback", "results/qwenpaw-rollback.json")
    print("QwenPaw rollback verified against saved backups and original provider metadata.")
    print(f"Restored per-agent selection: {original['provider_id']} / {original['model']}")
    if permanent_sync:
        print("The explicitly requested permanent oMLX credential sync was retained and verified.")
    print("The adapter and fused model were retained.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-id", default="default")
    parser.add_argument("--model-id")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--rollback", action="store_true")
    group.add_argument("--prepare-rollback", action="store_true")
    group.add_argument("--verify-rollback", action="store_true")
    group.add_argument("--sync-omlx-key", action="store_true")
    parser.add_argument("--skip-restart", action="store_true")
    args = parser.parse_args()
    if args.verify_rollback:
        if args.skip_restart or args.model_id:
            parser.error("--verify-rollback takes only --agent-id")
        verify_rollback(args.agent_id)
        return
    if args.prepare_rollback:
        if args.skip_restart or args.model_id:
            parser.error("--prepare-rollback takes only --agent-id")
        prepare_rollback(args.agent_id)
        return
    if args.sync_omlx_key:
        if args.skip_restart or args.model_id:
            parser.error("--sync-omlx-key takes only --agent-id")
        provider_state_command("--sync-current-key")
        print("Permanent oMLX credential synchronization verified; no key was printed.")
        return
    if args.rollback:
        if args.model_id:
            parser.error("--rollback and --model-id are mutually exclusive")
        prepared = RESULTS / "checkpoints" / "part8-prepared-rollback.json"
        already_prepared = prepared.exists()
        if args.skip_restart and not already_prepared:
            parser.error("Prepare rollback before using --skip-restart")
        if not already_prepared:
            prepare_rollback(args.agent_id)
        if not args.skip_restart:
            restart_daemon()
        verify_rollback(args.agent_id)
        return
    if args.skip_restart:
        parser.error("--skip-restart is only valid with --rollback")
    selected_path = RESULTS / "omlx-selected-model.json"
    model_id = args.model_id or json.loads(selected_path.read_text())["model_id"]
    select_model(args.agent_id, model_id)


if __name__ == "__main__":
    main()
