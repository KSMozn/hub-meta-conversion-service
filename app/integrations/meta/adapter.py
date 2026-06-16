"""Adapter interface for Meta Marketing API operations the Hub uses.

The whole point: every code path goes through this Protocol so that
``MockMetaAdapter`` (used in dev/tests) and ``RealMetaAdapter`` (production
Graph API calls) are interchangeable behind a single seam.
"""

from __future__ import annotations

from typing import Protocol

from app.integrations.meta.schemas import (
    CustomConversion,
    CustomConversionCreateInput,
    MetaPixel,
)


class MetaError(Exception):
    """Base for everything the adapter raises."""


class MetaAuthError(MetaError):
    """Token invalid/expired; caller should refresh and retry."""


class MetaRateLimitedError(MetaError):
    """HTTP 429 / app-rate-limit. ``retry_after_seconds`` is best-effort."""

    def __init__(self, message: str, retry_after_seconds: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class MetaNotFoundError(MetaError):
    """The referenced object (pixel, ad account, ...) doesn't exist."""


class MetaAdapter(Protocol):
    """The surface area the Hub needs from Meta.

    Anything we add to this protocol must be implemented by both adapters.
    """

    def list_pixels(self, *, ad_account_id: str, access_token: str) -> list[MetaPixel]: ...

    def create_custom_conversion(
        self,
        *,
        ad_account_id: str,
        access_token: str,
        payload: CustomConversionCreateInput,
    ) -> CustomConversion: ...
