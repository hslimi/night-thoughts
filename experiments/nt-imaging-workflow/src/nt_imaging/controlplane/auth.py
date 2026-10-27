from __future__ import annotations

import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from .db import ControlDB

password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


def hash_password(password: str) -> str:
    if len(password) < 12 or len(password) > 256:
        raise ValueError("Password length must be between 12 and 256 characters")
    return password_hasher.hash(password)


def verify_password(encoded: str, candidate: str) -> bool:
    try:
        return password_hasher.verify(encoded, candidate)
    except (VerifyMismatchError, VerificationError):
        return False


@dataclass
class AttemptWindow:
    failures: list[float] = field(default_factory=list)
    blocked_until: float = 0.0


class LoginLimiter:
    def __init__(self) -> None:
        self.attempts: dict[str, AttemptWindow] = defaultdict(AttemptWindow)

    def blocked(self, key: str) -> int:
        window = self.attempts[key]
        remaining = int(window.blocked_until - time.monotonic())
        return max(0, remaining)

    def failed(self, key: str) -> None:
        current = time.monotonic()
        window = self.attempts[key]
        window.failures = [stamp for stamp in window.failures if current - stamp < 900]
        window.failures.append(current)
        count = len(window.failures)
        if count >= 5:
            window.blocked_until = current + min(900, 2 ** min(count - 4, 8) * 15)
            window.failures = []

    def succeeded(self, key: str) -> None:
        self.attempts.pop(key, None)


def new_secrets() -> tuple[str, str]:
    return secrets.token_urlsafe(32), secrets.token_urlsafe(32)


def csrf_valid(db: ControlDB, session_token: str, csrf_token: str) -> bool:
    session = db.session(session_token)
    if not session:
        return False
    from .db import token_hash

    return secrets.compare_digest(session["csrf_hash"], token_hash(csrf_token))
