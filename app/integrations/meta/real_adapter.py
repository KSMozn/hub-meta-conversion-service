"""Adapter implementation that hits the real Meta Marketing API.

This class is fully wired but is not exercised by the test suite — flipping
``META_USE_MOCK=false`` (and supplying valid OAuth tokens) is the only thing
required for production.
"""

from __future__ import annotations

from app.integrations.meta.adapter import MetaAdapter
from app.integrations.meta.client import MetaApiClient
from app.integrations.meta.schemas import (
    CustomConversion,
    CustomConversionCreateInput,
    MetaPixel,
)


class RealMetaAdapter(MetaAdapter):
    def __init__(self, client: MetaApiClient) -> None:
        self._client = client

    def list_pixels(self, *, ad_account_id: str, access_token: str) -> list[MetaPixel]:
        # GET /{ad_account_id}/adspixels?fields=id,name,status
        data = self._client.get(
            f"/{ad_account_id}/adspixels",
            access_token=access_token,
            params={"fields": "id,name,status"},
        )
        items = data.get("data", []) if isinstance(data, dict) else []
        return [MetaPixel.model_validate(item) for item in items]

    def create_custom_conversion(
        self,
        *,
        ad_account_id: str,
        access_token: str,
        payload: CustomConversionCreateInput,
    ) -> CustomConversion:
        # POST /{ad_account_id}/customconversions
        body: dict = {
            "pixel_id": payload.pixel_id,
            "name": payload.name,
            "custom_event_type": payload.event_type,
            "category": payload.category,
        }
        if payload.value is not None:
            body["default_conversion_value"] = str(payload.value)
        if payload.currency is not None:
            body["default_conversion_currency"] = payload.currency
        if payload.rule is not None:
            body["rule"] = payload.rule.model_dump()

        data = self._client.post(
            f"/{ad_account_id}/customconversions",
            access_token=access_token,
            json=body,
        )
        return CustomConversion(
            id=str(data["id"]),
            pixel_id=payload.pixel_id,
            name=payload.name,
            event_type=payload.event_type,
            category=payload.category,
            value=payload.value,
            currency=payload.currency,
            rule=payload.rule.model_dump() if payload.rule else None,
        )
