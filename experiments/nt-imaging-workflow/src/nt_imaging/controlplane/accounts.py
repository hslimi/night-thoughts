from __future__ import annotations

import argparse
import getpass
import os
import re
import secrets

from ..config import Settings
from .auth import hash_password
from .db import ControlDB


def upsert_account(reset: bool) -> None:
    username = os.getenv("NT_DOCTOR_USERNAME") or input("Doctor username: ").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,64}", username):
        raise SystemExit(
            "Username must contain 3-64 letters, digits, dots, underscores, or hyphens"
        )
    password = os.getenv("NT_DOCTOR_PASSWORD")
    generated = False
    if not password:
        password = getpass.getpass("Initial password (leave blank to generate): ")
    if not password:
        password = secrets.token_urlsafe(18)
        generated = True
    settings = Settings.from_env()
    ControlDB(settings.data_root / "controlplane.sqlite3").upsert_user(
        username, hash_password(password)
    )
    print(
        f"{'Reset' if reset else 'Created'} doctor account {username!r}; existing sessions invalidated"
    )
    if generated:
        print(f"Initial password (shown once): {password}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    upsert_account(args.reset)


if __name__ == "__main__":
    main()
