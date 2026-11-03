"""Pseudonymous lookup key for OIDC identities stored in memberships."""

import base64
import hashlib
import hmac
import os


def identity_digest(issuer: str, subject: str) -> str:
    encoded_key = os.environ.get("IDENTITY_LOOKUP_KEY", "")
    try:
        key = base64.b64decode(encoded_key, validate=True)
    except (ValueError, TypeError, KeyError) as exc:
        raise RuntimeError("IDENTITY_LOOKUP_KEY must be base64-encoded 32-byte key material.") from exc
    if len(key) != 32:
        raise RuntimeError("IDENTITY_LOOKUP_KEY must be base64-encoded 32-byte key material.")
    message = f"{issuer}\0{subject}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()
