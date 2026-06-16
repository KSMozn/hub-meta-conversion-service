"""HTTP client used by the real Meta adapter.

Concerns lumped here on purpose:
* base URL + timeout from settings,
* retries with exponential backoff for 429 / 5xx,
* parsing Meta's error envelope into typed exceptions.

The mock adapter does NOT use this class — it constructs responses directly.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import Settings
from app.integrations.meta.adapter import (
    MetaAuthError,
    MetaError,
    MetaNotFoundError,
    MetaRateLimitedError,
)

logger = logging.getLogger(__name__)


def _log_retry(state: RetryCallState) -> None:
    if state.outcome and state.outcome.failed:
        logger.warning(
            "meta_api_retry",
            extra={
                "attempt": state.attempt_number,
                "exception": repr(state.outcome.exception()),
            },
        )


class MetaApiClient:
    """Thin wrapper around ``httpx.Client`` with Meta-flavored error mapping."""

    def __init__(self, settings: Settings, http_client: httpx.Client | None = None) -> None:
        self._settings = settings
        self._client = http_client or httpx.Client(
            base_url=settings.meta_api_base_url,
            timeout=settings.meta_api_timeout_seconds,
        )

    def close(self) -> None:
        self._client.close()

    def get(self, path: str, *, access_token: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, access_token=access_token, params=params)

    def post(self, path: str, *, access_token: str, json: dict[str, Any]) -> Any:
        return self._request("POST", path, access_token=access_token, json=json)

    def _request(
        self,
        method: str,
        path: str,
        *,
        access_token: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        retrying = retry(
            reraise=True,
            stop=stop_after_attempt(self._settings.meta_max_retries),
            wait=wait_exponential(
                multiplier=self._settings.meta_retry_base_delay_seconds,
                min=self._settings.meta_retry_base_delay_seconds,
                max=10.0,
            ),
            retry=retry_if_exception_type((MetaRateLimitedError, httpx.TransportError)),
            after=_log_retry,
        )
        return retrying(self._do_request)(
            method, path, access_token=access_token, params=params, json=json
        )

    def _do_request(
        self,
        method: str,
        path: str,
        *,
        access_token: str,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
    ) -> Any:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self._client.request(
            method, path, params=params, json=json, headers=headers
        )
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise MetaRateLimitedError(
                "Meta API rate limited",
                retry_after_seconds=float(retry_after) if retry_after else None,
            )
        if response.status_code in (401, 403):
            raise MetaAuthError(self._extract_error(response))
        if response.status_code == 404:
            raise MetaNotFoundError(self._extract_error(response))
        if response.status_code >= 500:
            # treat as transient; map to rate-limited so it's retried
            raise MetaRateLimitedError(f"Meta API {response.status_code}: server error")
        if response.status_code >= 400:
            raise MetaError(self._extract_error(response))
        return response.json()

    @staticmethod
    def _extract_error(response: httpx.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            return response.text or f"HTTP {response.status_code}"
        err = body.get("error", {}) if isinstance(body, dict) else {}
        if isinstance(err, dict) and err:
            return f"{err.get('code')}/{err.get('type')}: {err.get('message')}"
        return str(body)
