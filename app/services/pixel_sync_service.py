from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.integrations.meta.adapter import MetaAdapter
from app.repositories.advertiser import AdvertiserRepository
from app.repositories.pixel import PixelRepository
from app.services.exceptions import NotFoundError, UpstreamError
from app.services.oauth_service import META_PROVIDER, OAuthService

logger = logging.getLogger(__name__)


class PixelSyncService:
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
        self.pixels = PixelRepository(session)

    def sync_for_advertiser(
        self, advertiser_id: uuid.UUID
    ) -> tuple[list, int, int]:
        """Fetch pixels from Meta and reconcile with our DB.

        Returns (pixels, created_count, updated_count).
        """
        advertiser = self.advertisers.get(advertiser_id)
        if advertiser is None:
            raise NotFoundError(f"advertiser {advertiser_id} not found")
        if not advertiser.meta_ad_account_id:
            raise UpstreamError(
                f"advertiser {advertiser_id} has no meta_ad_account_id set"
            )

        token = self.oauth.get_access_token(advertiser_id, provider=META_PROVIDER)
        fetched = self.meta.list_pixels(
            ad_account_id=advertiser.meta_ad_account_id, access_token=token.value
        )

        created = 0
        updated = 0
        for meta_pixel in fetched:
            _, was_created = self.pixels.upsert_from_meta(
                advertiser_id=advertiser.id,
                meta_pixel_id=meta_pixel.id,
                name=meta_pixel.name,
                status=meta_pixel.status,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        logger.info(
            "pixel_sync_completed",
            extra={
                "advertiser_id": str(advertiser_id),
                "fetched": len(fetched),
                "created": created,
                "updated": updated,
            },
        )
        return self.pixels.list_for_advertiser(advertiser_id), created, updated
