from __future__ import annotations

import pytest

from app.core.security import TokenCipher


def test_token_cipher_roundtrip() -> None:
    cipher = TokenCipher("a-very-secret-key")
    plaintext = "EAAB1234refreshtoken"
    assert cipher.decrypt(cipher.encrypt(plaintext)) == plaintext


def test_token_cipher_rejects_tampered_payload() -> None:
    cipher = TokenCipher("a-very-secret-key")
    token = cipher.encrypt("hello")
    # Flip a single byte in the ciphertext segment.
    tampered = token[:-2] + ("A" if token[-2] != "A" else "B") + token[-1]
    with pytest.raises(ValueError):
        cipher.decrypt(tampered)


def test_token_cipher_requires_key() -> None:
    with pytest.raises(ValueError):
        TokenCipher("")
