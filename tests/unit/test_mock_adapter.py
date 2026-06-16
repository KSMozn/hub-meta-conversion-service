from __future__ import annotations

from decimal import Decimal

import pytest

from app.integrations.meta.adapter import MetaNotFoundError, MetaRateLimitedError
from app.integrations.meta.mock_adapter import MockMetaAdapter
from app.integrations.meta.schemas import CustomConversionCreateInput, MetaPixel


def _adapter_with_pixel() -> MockMetaAdapter:
    a = MockMetaAdapter()
    a.seed_pixels("act_1", [MetaPixel(id="pix_1", name="Web", status="ACTIVE")])
    return a


def test_list_pixels_returns_seeded_pixels() -> None:
    adapter = _adapter_with_pixel()
    pixels = adapter.list_pixels(ad_account_id="act_1", access_token="t")
    assert [p.id for p in pixels] == ["pix_1"]


def test_create_custom_conversion_is_name_idempotent() -> None:
    adapter = _adapter_with_pixel()
    payload = CustomConversionCreateInput(
        pixel_id="pix_1",
        name="Checkout Purchase",
        event_type="Purchase",
        category="purchase",
        value=Decimal("9.99"),
        currency="USD",
    )
    first = adapter.create_custom_conversion(
        ad_account_id="act_1", access_token="t", payload=payload
    )
    second = adapter.create_custom_conversion(
        ad_account_id="act_1", access_token="t", payload=payload
    )
    assert first.id == second.id
    assert len(adapter.conversions()) == 1


def test_create_custom_conversion_rejects_unknown_pixel() -> None:
    adapter = _adapter_with_pixel()
    payload = CustomConversionCreateInput(
        pixel_id="pix_unknown",
        name="x",
        event_type="Purchase",
        category="purchase",
    )
    with pytest.raises(MetaNotFoundError):
        adapter.create_custom_conversion(
            ad_account_id="act_1", access_token="t", payload=payload
        )


def test_rate_limit_every_triggers_rate_limit_error() -> None:
    adapter = MockMetaAdapter(rate_limit_every=2)
    adapter.seed_pixels("act_1", [MetaPixel(id="pix_1", name="Web")])
    adapter.list_pixels(ad_account_id="act_1", access_token="t")  # 1st - ok
    with pytest.raises(MetaRateLimitedError):
        adapter.list_pixels(ad_account_id="act_1", access_token="t")  # 2nd - boom
