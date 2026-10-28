from __future__ import annotations

import argparse
import getpass
import os
import re
import secrets
from pathlib import Path

from .auth import hash_password, verify_password
from .db import ControlDB, fingerprint

CANONICAL_ROOT = Path(__file__).resolve().parents[3]
OBSOLETE_ROOT = Path("/Users/night-thoughts/healthcare/nt-imaging-workflow/var")


def upsert_account(reset: bool, data_root: Path | None = None) -> int:
    target_root = (data_root or CANONICAL_ROOT / "var").expanduser().resolve()
    if target_root == OBSOLETE_ROOT or OBSOLETE_ROOT in target_root.parents:
        raise SystemExit("Refusing to modify the obsolete installation")
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
    database = target_root / "controlplane.sqlite3"
    print(f"Canonical runtime: {CANONICAL_ROOT}")
    print(f"Target database fingerprint before: {fingerprint(database)}")
    db = ControlDB(database)
    db.upsert_user(username, hash_password(password))
    current = db.user(username)
    if not current or not verify_password(current["password_hash"], password):
        raise SystemExit("Account verification failed")
    print(f"Target database fingerprint after: {fingerprint(database)}")
    print(f"{'Reset' if reset else 'Created'} doctor account {username!r}")
    print(f"Sessions invalidated: {db.last_invalidated_sessions}")
    print("New credentials are effective immediately; no service restart was performed")
    if generated:
        print(f"Initial password (shown once): {password}")
    return db.last_invalidated_sessions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--data-root", type=Path)
    args = parser.parse_args()
    upsert_account(args.reset, args.data_root)


if __name__ == "__main__":
    main()
