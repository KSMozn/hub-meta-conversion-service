"""The httpx-level retry path on the real Meta client.

We don't hit the network — we mount an httpx ``MockTransport`` and assert the
client retries until it succeeds within ``META_MAX_RETRIES``.
"""

from __future__ import annotations

import httpx
import pytest

from app.core.config import Settings
from app.integrations.meta.adapter import MetaAuthError, MetaRateLimitedError
from app.integrations.meta.client import MetaApiClient


def _settings(**overrides: object) -> Settings:
    defaults = dict(
        meta_max_retries=3,
        meta_retry_base_delay_seconds=0.0,  # don't sleep in tests
    )
    defaults.update(overrides)  # type: ignore[arg-type]
    return Settings(**defaults)  # type: ignore[arg-type]


def _client_with_transport(transport: httpx.MockTransport, settings: Settings) -> MetaApiClient:
    http = httpx.Client(transport=transport, base_url=settings.meta_api_base_url)
    return MetaApiClient(settings, http_client=http)


def test_retries_on_429_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={"error": "x"})
        return httpx.Response(200, json={"ok": True})

    settings = _settings()
    client = _client_with_transport(httpx.MockTransport(handler), settings)
    try:
        result = client.get("/anything", access_token="t")
        assert result == {"ok": True}
        assert calls["n"] == 3
    finally:
        client.close()


def test_exhausts_retries_and_raises_rate_limit() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "0"}, json={"error": "x"})

    settings = _settings(meta_max_retries=2)
    client = _client_with_transport(httpx.MockTransport(handler), settings)
    try:
        with pytest.raises(MetaRateLimitedError):
            client.get("/anything", access_token="t")
    finally:
        client.close()


def test_auth_error_not_retried() -> None:
    calls = {"n": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(
            401, json={"error": {"code": 190, "type": "OAuthException", "message": "expired"}}
        )

    settings = _settings()
    client = _client_with_transport(httpx.MockTransport(handler), settings)
    try:
        with pytest.raises(MetaAuthError):
            client.get("/anything", access_token="t")
        assert calls["n"] == 1
    finally:
        client.close()
