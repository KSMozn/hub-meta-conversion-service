"""FastAPI dependency wiring.

The Meta adapter is held on ``app.state`` so tests can swap in a ``MockMetaAdapter``
instance with their own seeded state.
"""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.integrations.meta.adapter import MetaAdapter
from app.services.advertiser_service import AdvertiserService
from app.services.conversion_tag_service import ConversionTagService
from app.services.idempotency import IdempotencyService
from app.services.oauth_service import OAuthService
from app.services.pixel_sync_service import PixelSyncService


def get_settings_dep() -> Settings:
    return get_settings()


def get_meta_adapter(request: Request) -> MetaAdapter:
    adapter: MetaAdapter | None = getattr(request.app.state, "meta_adapter", None)
    if adapter is None:
        raise RuntimeError("meta adapter not configured on app.state")
    return adapter


def get_oauth_service(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings_dep),
) -> OAuthService:
    return OAuthService(session, settings)


def get_advertiser_service(session: Session = Depends(get_session)) -> AdvertiserService:
    return AdvertiserService(session)


def get_pixel_sync_service(
    session: Session = Depends(get_session),
    meta: MetaAdapter = Depends(get_meta_adapter),
    oauth: OAuthService = Depends(get_oauth_service),
) -> PixelSyncService:
    return PixelSyncService(session, meta=meta, oauth=oauth)


def get_conversion_tag_service(
    session: Session = Depends(get_session),
    meta: MetaAdapter = Depends(get_meta_adapter),
    oauth: OAuthService = Depends(get_oauth_service),
) -> ConversionTagService:
    return ConversionTagService(session, meta=meta, oauth=oauth)


def get_idempotency_service(session: Session = Depends(get_session)) -> IdempotencyService:
    return IdempotencyService(session)
