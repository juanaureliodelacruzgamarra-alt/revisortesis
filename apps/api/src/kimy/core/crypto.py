"""Symmetric encryption for secrets at rest (ORCID tokens, Copyleaks API key…).

Uses Fernet (AES-128-CBC + HMAC) keyed off settings.encryption_key. The key
must be a URL-safe base64-encoded 32-byte blob. If the configured key isn't a
valid Fernet key we derive one deterministically via SHA-256 — that's NOT
production-grade rotation but lets dev environments work with arbitrary
ENCRYPTION_KEY values.
"""
from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from kimy.core.config import get_settings


class DecryptionError(Exception):
    pass


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    settings = get_settings()
    raw = settings.encryption_key or ""
    try:
        # If the key is already a valid Fernet key, just use it.
        return Fernet(raw.encode())
    except (ValueError, TypeError):
        # Derive a key deterministically from the configured passphrase.
        digest = hashlib.sha256(raw.encode("utf-8")).digest()
        derived = base64.urlsafe_b64encode(digest)
        return Fernet(derived)


def encrypt(plaintext: str) -> bytes:
    return _fernet().encrypt(plaintext.encode("utf-8"))


def decrypt(ciphertext: bytes) -> str:
    try:
        return _fernet().decrypt(ciphertext).decode("utf-8")
    except InvalidToken as exc:
        raise DecryptionError("invalid token (wrong key or tampered data)") from exc
