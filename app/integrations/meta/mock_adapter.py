"""In-memory mock of the Meta Marketing API.

Goals:
* Deterministic by default so tests are stable.
* Optional fault injection (``fail_rate``, ``rate_limit_every``) so we can prove
  the retry/backoff path in tests.
* Same Protocol as the real adapter — services depend only on ``MetaAdapter``.
"""

from __future__ import annotations

import hashlib
import threading
from collections import defaultdict

from app.integrations.meta.adapter import MetaAdapter, MetaNotFoundError, MetaRateLimitedError
from app.integrations.meta.schemas import (
    CustomConversion,
    CustomConversionCreateInput,
    MetaPixel,
)


class MockMetaAdapter(MetaAdapter):
    def __init__(
        self,
        *,
        rate_limit_every: int = 0,
        fail_rate: float = 0.0,
    ) -> None:
        self._lock = threading.Lock()
        self._pixels: dict[str, list[MetaPixel]] = defaultdict(list)
        self._conversions: dict[str, CustomConversion] = {}
        self._conversions_by_name: dict[tuple[str, str], CustomConversion] = {}
        self._rate_limit_every = rate_limit_every
        self._fail_rate = fail_rate
        self._call_counter = 0

    # ----- helpers used only in tests/dev -----

    def seed_pixels(self, ad_account_id: str, pixels: list[MetaPixel]) -> None:
        with self._lock:
            self._pixels[ad_account_id] = list(pixels)

    def conversions(self) -> list[CustomConversion]:
        return list(self._conversions.values())

    # ----- adapter API -----

    def list_pixels(self, *, ad_account_id: str, access_token: str) -> list[MetaPixel]:
        self._maybe_fail()
        with self._lock:
            return list(self._pixels.get(ad_account_id, []))

    def create_custom_conversion(
        self,
        *,
        ad_account_id: str,
        access_token: str,
        payload: CustomConversionCreateInput,
    ) -> CustomConversion:
        self._maybe_fail()
        with self._lock:
            if payload.pixel_id not in {p.id for p in self._pixels.get(ad_account_id, [])}:
                raise MetaNotFoundError(
                    f"pixel {payload.pixel_id} not found on account {ad_account_id}"
                )
            # Meta itself is name-unique per ad account; replicate that here.
            existing = self._conversions_by_name.get((ad_account_id, payload.name))
            if existing is not None:
                return existing

            conv_id = _stable_id("cc", ad_account_id, payload.name)
            conv = CustomConversion(
                id=conv_id,
                pixel_id=payload.pixel_id,
                name=payload.name,
                event_type=payload.event_type,
                category=payload.category,
                value=payload.value,
                currency=payload.currency,
                rule=payload.rule.model_dump() if payload.rule else None,
            )
            self._conversions[conv_id] = conv
            self._conversions_by_name[(ad_account_id, payload.name)] = conv
            return conv

    # ----- fault injection -----

    def _maybe_fail(self) -> None:
        with self._lock:
            self._call_counter += 1
            counter = self._call_counter
        if self._rate_limit_every and counter % self._rate_limit_every == 0:
            raise MetaRateLimitedError("mock rate limit", retry_after_seconds=0.01)
        # Deterministic-ish failure: every Nth call when fail_rate > 0
        if self._fail_rate > 0:
            threshold = max(1, int(round(1.0 / self._fail_rate)))
            if counter % threshold == 0:
                raise MetaRateLimitedError("mock transient error", retry_after_seconds=0.01)


def _stable_id(prefix: str, *parts: str) -> str:
    h = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{h}"
