from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.oauth_token import OAuthToken


class OAuthTokenRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, advertiser_id: uuid.UUID, provider: str) -> OAuthToken | None:
        stmt = select(OAuthToken).where(
            OAuthToken.advertiser_id == advertiser_id,
            OAuthToken.provider == provider,
        )
        return self.session.scalar(stmt)

    def upsert(
        self,
        *,
        advertiser_id: uuid.UUID,
        provider: str,
        access_token_encrypted: str,
        refresh_token_encrypted: str | None,
        expires_at: datetime,
        scopes: str | None,
    ) -> OAuthToken:
        existing = self.get(advertiser_id, provider)
        if existing is None:
            token = OAuthToken(
                advertiser_id=advertiser_id,
                provider=provider,
                access_token_encrypted=access_token_encrypted,
                refresh_token_encrypted=refresh_token_encrypted,
                expires_at=expires_at,
                scopes=scopes,
            )
            self.session.add(token)
            self.session.flush()
            return token

        existing.access_token_encrypted = access_token_encrypted
        if refresh_token_encrypted is not None:
            existing.refresh_token_encrypted = refresh_token_encrypted
        existing.expires_at = expires_at
        if scopes is not None:
            existing.scopes = scopes
        self.session.flush()
        return existing
