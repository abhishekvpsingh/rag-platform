"""Authenticated credential envelopes bound to tenant and connection identifiers."""

import base64
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True)
class CredentialCipher:
    keys: Mapping[str, bytes] = field(repr=False)
    active_key: str

    def __post_init__(self) -> None:
        if self.active_key not in self.keys or any(len(key) != 32 for key in self.keys.values()):
            raise ValueError("Invalid credential key configuration")

    @staticmethod
    def context(tenant_id: str, connection_id: str) -> bytes:
        return json.dumps([tenant_id, connection_id], separators=(",", ":")).encode()

    def encrypt(self, secret: str, tenant_id: str, connection_id: str) -> str:
        if not secret or len(secret.encode()) > 16000:
            raise ValueError("Invalid credential size")
        nonce = os.urandom(12)
        encrypted = AESGCM(self.keys[self.active_key]).encrypt(
            nonce, secret.encode(), self.context(tenant_id, connection_id)
        )
        return json.dumps([self.active_key, base64.b64encode(nonce + encrypted).decode()])

    def decrypt(self, envelope: str, tenant_id: str, connection_id: str) -> str:
        try:
            key_id, encoded = json.loads(envelope)
            blob = base64.b64decode(encoded, validate=True)
            return (
                AESGCM(self.keys[key_id])
                .decrypt(blob[:12], blob[12:], self.context(tenant_id, connection_id))
                .decode()
            )
        except (ValueError, KeyError, TypeError, InvalidTag, UnicodeError):
            raise ValueError("Credential unavailable") from None

    def rotate(self, envelope: str, tenant_id: str, connection_id: str) -> str:
        return self.encrypt(
            self.decrypt(envelope, tenant_id, connection_id), tenant_id, connection_id
        )
