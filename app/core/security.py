"""Token encryption helpers.

OAuth refresh/access tokens are encrypted at rest. The implementation uses a
simple XOR-with-key + base64 scheme so the POC has no native-crypto dependency,
but the interface (``encrypt``/``decrypt``) mirrors what a Fernet/KMS backend
would expose so production swap-in is a one-file change.
"""

from __future__ import annotations

import base64
import hashlib
import hmac


class TokenCipher:
    """Symmetric encrypt/decrypt with HMAC integrity for OAuth tokens.

    Production note: replace with ``cryptography.fernet.Fernet`` or a KMS-backed
    envelope-encryption helper. The repository contract (str -> str) stays the
    same, so callers don't change.
    """

    def __init__(self, key: str) -> None:
        if not key:
            raise ValueError("token encryption key must be non-empty")
        self._key = hashlib.sha256(key.encode("utf-8")).digest()

    def encrypt(self, plaintext: str) -> str:
        data = plaintext.encode("utf-8")
        ciphertext = self._xor(data)
        mac = hmac.new(self._key, ciphertext, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(mac + ciphertext).decode("ascii")

    def decrypt(self, token: str) -> str:
        raw = base64.urlsafe_b64decode(token.encode("ascii"))
        mac, ciphertext = raw[:32], raw[32:]
        expected = hmac.new(self._key, ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected):
            raise ValueError("token integrity check failed")
        return self._xor(ciphertext).decode("utf-8")

    def _xor(self, data: bytes) -> bytes:
        key = self._key
        return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
