from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from app.core.config import get_settings
from app.models.advertiser import Advertiser
from app.services.oauth_service import META_PROVIDER, OAuthService

pytestmark = pytest.mark.integration


def test_get_access_token_refreshes_when_near_expiry(db_session) -> None:
    settings = get_settings()
    advertiser = Advertiser(
        name="X", external_ref=f"ext-{uuid.uuid4()}", meta_ad_account_id="act_1"
    )
    db_session.add(advertiser)
    db_session.flush()

    svc = OAuthService(db_session, settings)
    # Store with a TTL well below the refresh leeway -> next read must refresh.
    svc.store_initial_token(
        advertiser_id=advertiser.id,
        access_token="initial",
        refresh_token="refresh-1",
        ttl=timedelta(seconds=1),
    )
    db_session.commit()

    token = svc.get_access_token(advertiser.id, provider=META_PROVIDER)
    assert token.value != "initial"
    assert token.value.startswith("mock-access-")


def test_get_access_token_returns_cached_when_fresh(db_session) -> None:
    settings = get_settings()
    advertiser = Advertiser(name="Y", external_ref=f"ext-{uuid.uuid4()}")
    db_session.add(advertiser)
    db_session.flush()

    svc = OAuthService(db_session, settings)
    svc.store_initial_token(
        advertiser_id=advertiser.id,
        access_token="still-fresh",
        refresh_token="r",
        ttl=timedelta(hours=1),
    )
    db_session.commit()

    assert svc.get_access_token(advertiser.id).value == "still-fresh"
