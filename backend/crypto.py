"""Authenticated encryption for workspace text fields.

The configured key ring contains base64-encoded 32-byte master keys. A
tenant-specific AES-GCM key is derived from each master key, so ciphertext
cannot be moved between tenants or records without failing authentication.
"""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class EncryptionConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class EncryptedValue:
    key_id: str
    nonce: bytes
    ciphertext: bytes


def _key_ring() -> tuple[dict[str, bytes], str]:
    raw = os.environ.get("DATA_ENCRYPTION_KEYS_JSON", "")
    active_id = os.environ.get("DATA_ENCRYPTION_ACTIVE_KEY", "")
    try:
        encoded_keys = json.loads(raw)
        if not isinstance(encoded_keys, dict):
            raise ValueError("Key ring must be a JSON object.")
        keys = {key_id: base64.b64decode(value, validate=True) for key_id, value in encoded_keys.items()}
    except (ValueError, TypeError, AttributeError) as exc:
        raise EncryptionConfigurationError("Invalid data encryption key configuration.") from exc
    if not keys or active_id not in keys or any(len(key) != 32 for key in keys.values()):
        raise EncryptionConfigurationError("A valid active 32-byte data encryption key is required.")
    return keys, active_id


def _tenant_key(master_key: bytes, tenant_id: str) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=tenant_id.encode("ascii"),
        info=b"deeplitics/workspace-item/v1",
    ).derive(master_key)


def encrypt_text(tenant_id: str, record_id: str, plaintext: str, field: str = "content") -> EncryptedValue:
    import secrets

    keys, active_id = _key_ring()
    nonce = secrets.token_bytes(12)
    aad = f"v1:{tenant_id}:{record_id}:{field}".encode("ascii")
    ciphertext = AESGCM(_tenant_key(keys[active_id], tenant_id)).encrypt(
        nonce, plaintext.encode("utf-8"), aad
    )
    return EncryptedValue(active_id, nonce, ciphertext)


def decrypt_text(tenant_id: str, record_id: str, value: EncryptedValue, field: str = "content") -> str:
    keys, _ = _key_ring()
    master_key = keys.get(value.key_id)
    if master_key is None:
        raise EncryptionConfigurationError("The key required to decrypt this record is unavailable.")
    aad = f"v1:{tenant_id}:{record_id}:{field}".encode("ascii")
    return AESGCM(_tenant_key(master_key, tenant_id)).decrypt(
        value.nonce, value.ciphertext, aad
    ).decode("utf-8")
