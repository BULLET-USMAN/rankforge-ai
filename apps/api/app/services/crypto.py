"""Cryptographic helper utilities for encrypting sensitive credentials at rest."""

from __future__ import annotations

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.logging import logger


def _get_fernet() -> Fernet:
    """Derives a deterministic 32-byte Fernet key from the configured SECRET_KEY."""
    secret = settings.SECRET_KEY or "fallback_secret_key_for_testing_32chars"
    key_bytes = hashlib.sha256(secret.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def encrypt_secret(plain_text: Optional[str]) -> Optional[str]:
    """Encrypts a plaintext secret string using Fernet (AES-128-CBC + HMAC)."""
    if not plain_text:
        return None
    try:
        fernet = _get_fernet()
        return fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")
    except Exception as exc:
        logger.error(f"Failed to encrypt secret: {exc}")
        raise ValueError("Could not safely encrypt sensitive credential.") from exc


def decrypt_secret(cipher_text: Optional[str]) -> Optional[str]:
    """Decrypts a Fernet ciphertext back to plaintext."""
    if not cipher_text:
        return None
    try:
        fernet = _get_fernet()
        return fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        logger.error("Failed to decrypt secret: invalid token or altered key.")
        raise ValueError("Decryption failed: corrupted credential or mismatching secret key.")
    except Exception as exc:
        logger.error(f"Failed to decrypt secret: {exc}")
        raise ValueError("Could not decrypt credential.") from exc
