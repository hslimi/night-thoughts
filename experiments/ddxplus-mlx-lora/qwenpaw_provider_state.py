import argparse
import asyncio
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from qwenpaw.providers.provider_manager import ProviderManager

ROOT = Path(__file__).resolve().parent
STATE = ROOT / "results" / "qwenpaw-credential-sync.json"
CONFIG_URL = "http://127.0.0.1:8088/api/models/omlx/config"


def manager():
    instance = ProviderManager.get_instance()
    if instance.get_provider("omlx") is None:
        raise RuntimeError("The installed oMLX provider was not found")
    return instance


def current_omlx_key():
    settings = json.loads((Path.home() / ".omlx" / "settings.json").read_text())
    key = settings["auth"]["api_key"]
    if not isinstance(key, str) or not key:
        raise ValueError("The current oMLX API key is missing or invalid")
    return key


def verify_current_key():
    provider = manager().load_provider("omlx", is_builtin=False)
    if provider is None or provider.api_key != current_omlx_key():
        raise RuntimeError("QwenPaw's saved oMLX credential does not match the current oMLX key")


def sync_current_key():
    provider = manager().get_provider("omlx")
    original_url = provider.base_url
    original_protocol = provider.chat_model
    request = urllib.request.Request(
        CONFIG_URL,
        method="PUT",
        data=json.dumps({"api_key": current_omlx_key(), "auto_discover": False}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)
    if result["base_url"] != original_url or result["chat_model"] != original_protocol:
        raise RuntimeError("An oMLX connection setting changed unexpectedly")
    verify_current_key()
    STATE.write_text(
        json.dumps(
            {
                "status": "synchronized_permanently",
                "permanent": True,
                "restore_original_credential_during_rollback": False,
                "persistent_credential_matches_current_omlx": True,
                "credential_values_recorded": False,
                "synchronized_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
        + "\n"
    )
    STATE.chmod(0o600)
    print("QwenPaw's saved oMLX key now matches the existing oMLX key.")
    print("This is a persistent credential change; no original key will be restored during rollback.")
    print("No credential value was printed or included in the result file.")


async def restore_removed_models(model_ids):
    instance = manager()
    provider = instance.get_provider("omlx")
    original_key = provider.api_key
    original_url = provider.base_url
    original_protocol = provider.chat_model
    updated = await instance.update_provider_async(
        "omlx",
        {"removed_model_ids": model_ids},
    )
    restored = instance.get_provider("omlx")
    if not updated or restored.removed_model_ids != model_ids:
        raise RuntimeError("QwenPaw did not save the restored removal list")
    if (
        restored.api_key != original_key
        or restored.base_url != original_url
        or restored.chat_model != original_protocol
    ):
        raise RuntimeError("An oMLX connection setting changed unexpectedly")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--removed-model-ids")
    group.add_argument("--sync-current-key", action="store_true")
    group.add_argument("--verify-current-key", action="store_true")
    args = parser.parse_args()
    if args.removed_model_ids is not None:
        model_ids = json.loads(args.removed_model_ids)
        if not isinstance(model_ids, list) or not all(
            isinstance(model_id, str) and model_id for model_id in model_ids
        ):
            raise ValueError("Expected a list of model IDs")
        asyncio.run(restore_removed_models(model_ids))
        print("QwenPaw's saved oMLX removal list was restored without changing connection settings.")
    elif args.sync_current_key:
        sync_current_key()
    else:
        verify_current_key()
        print("QwenPaw's saved oMLX credential matches the current oMLX key.")


if __name__ == "__main__":
    main()
