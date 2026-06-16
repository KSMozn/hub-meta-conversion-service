from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.integrations.meta.adapter import MetaAdapter, MetaError
from app.integrations.meta.schemas import (
    CustomConversionCreateInput,
    CustomConversionRuleInput,
)
from app.models.conversion_tag import ConversionTag
from app.models.pixel import Pixel
from app.repositories.advertiser import AdvertiserRepository
from app.repositories.conversion_tag import ConversionTagRepository
from app.schemas.conversion_tag import ConversionTagCreate
from app.services.exceptions import ConflictError, NotFoundError, UpstreamError
from app.services.oauth_service import META_PROVIDER, OAuthService

logger = logging.getLogger(__name__)


class ConversionTagService:
    """Creates a Hub-owned conversion tag and a matching custom conversion in Meta.

    Order of operations matters: we insert a ``PENDING`` row first (and uniqueness
    catches double-creates), call Meta, then mark the row ``ACTIVE`` with the
    returned id. If Meta fails we leave the ``PENDING`` row in place so retries are
    idempotent at the Hub layer too — the same call from the client returns the
    same internal id rather than a fresh PENDING row.
    """

    def __init__(
        self,
        session: Session,
        *,
        meta: MetaAdapter,
        oauth: OAuthService,
    ) -> None:
        self.session = session
        self.meta = meta
        self.oauth = oauth
        self.advertisers = AdvertiserRepository(session)
        self.tags = ConversionTagRepository(session)

    def create(
        self, advertiser_id: uuid.UUID, payload: ConversionTagCreate
    ) -> ConversionTag:
        advertiser = self.advertisers.get(advertiser_id)
        if advertiser is None:
            raise NotFoundError(f"advertiser {advertiser_id} not found")
        if not advertiser.meta_ad_account_id:
            raise UpstreamError(
                f"advertiser {advertiser_id} has no meta_ad_account_id set"
            )

        pixel = self.session.get(Pixel, payload.pixel_id)
        if pixel is None or pixel.advertiser_id != advertiser_id:
            raise NotFoundError(
                f"pixel {payload.pixel_id} not found for advertiser {advertiser_id}"
            )

        existing = self.tags.get_by_advertiser_and_name(advertiser_id, payload.name)
        if existing is not None:
            # Replay-safe: same (advertiser, name) is treated as the same tag.
            if existing.status == "ACTIVE":
                return existing
            tag = existing
        else:
            tag = ConversionTag(
                advertiser_id=advertiser_id,
                pixel_id=pixel.id,
                name=payload.name,
                event_type=payload.event_type,
                category=payload.category,
                value=payload.value,
                currency=payload.currency,
                rule=payload.rule.model_dump() if payload.rule else None,
                status="PENDING",
            )
            try:
                self.tags.create(tag)
            except Exception as exc:
                self.session.rollback()
                raise ConflictError(
                    f"conversion tag {payload.name!r} already exists"
                ) from exc

        token = self.oauth.get_access_token(advertiser_id, provider=META_PROVIDER)
        meta_input = CustomConversionCreateInput(
            pixel_id=pixel.meta_pixel_id,
            name=payload.name,
            event_type=payload.event_type,
            category=payload.category,
            value=payload.value,
            currency=payload.currency,
            rule=(
                CustomConversionRuleInput(**payload.rule.model_dump())
                if payload.rule
                else None
            ),
        )
        try:
            created = self.meta.create_custom_conversion(
                ad_account_id=advertiser.meta_ad_account_id,
                access_token=token.value,
                payload=meta_input,
            )
        except MetaError as exc:
            logger.warning(
                "meta_create_custom_conversion_failed",
                extra={
                    "advertiser_id": str(advertiser_id),
                    "tag_id": str(tag.id),
                    "error": repr(exc),
                },
            )
            tag.status = "FAILED"
            tag.payload = meta_input.model_dump(mode="json")
            self.session.flush()
            raise UpstreamError(f"meta: {exc}") from exc

        tag.meta_custom_conversion_id = created.id
        tag.status = "ACTIVE"
        tag.payload = meta_input.model_dump(mode="json")
        self.session.flush()
        return tag

    def list_for_advertiser(self, advertiser_id: uuid.UUID) -> list[ConversionTag]:
        advertiser = self.advertisers.get(advertiser_id)
        if advertiser is None:
            raise NotFoundError(f"advertiser {advertiser_id} not found")
        return self.tags.list_for_advertiser(advertiser_id)
