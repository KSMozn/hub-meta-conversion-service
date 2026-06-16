"""OAuth2 token storage and refresh.

A real implementation would POST to ``oauth/access_token`` to swap the long-lived
refresh token for a fresh short-lived access token. Here we simulate that flow
deterministically so the rest of the system can be exercised end-to-end without
secrets. The seam to swap is ``_refresh_with_provider``.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import TokenCipher
from app.repositories.oauth_token import OAuthTokenRepository
from app.services.exceptions import NotFoundError

logger = logging.getLogger(__name__)

META_PROVIDER = "meta"

_DEFAULT_TTL = timedelta(hours=1)
# When the cached access token expires within this many seconds, refresh now
# instead of risking a 401 from Meta after the call leaves the process.
_REFRESH_LEEWAY_SECONDS = 60


@dataclass(slots=True)
class AccessToken:
    value: str
    expires_at: datetime


class OAuthService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.cipher = TokenCipher(settings.token_encryption_key)
        self.repo = OAuthTokenRepository(session)

    def store_initial_token(
        self,
        *,
        advertiser_id: uuid.UUID,
        access_token: str,
        refresh_token: str | None,
        ttl: timedelta = _DEFAULT_TTL,
        scopes: str | None = None,
        provider: str = META_PROVIDER,
    ) -> None:
        self.repo.upsert(
            advertiser_id=advertiser_id,
            provider=provider,
            access_token_encrypted=self.cipher.encrypt(access_token),
            refresh_token_encrypted=(
                self.cipher.encrypt(refresh_token) if refresh_token else None
            ),
            expires_at=datetime.now(timezone.utc) + ttl,
            scopes=scopes,
        )

    def get_access_token(
        self, advertiser_id: uuid.UUID, *, provider: str = META_PROVIDER
    ) -> AccessToken:
        token = self.repo.get(advertiser_id, provider)
        if token is None:
            raise NotFoundError(
                f"no {provider} oauth token stored for advertiser {advertiser_id}"
            )

        now = datetime.now(timezone.utc)
        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if (expires_at - now).total_seconds() > _REFRESH_LEEWAY_SECONDS:
            return AccessToken(
                value=self.cipher.decrypt(token.access_token_encrypted),
                expires_at=expires_at,
            )

        if token.refresh_token_encrypted is None:
            raise NotFoundError(
                f"{provider} token for advertiser {advertiser_id} expired with no refresh token"
            )

        logger.info(
            "oauth_token_refresh",
            extra={"advertiser_id": str(advertiser_id), "provider": provider},
        )
        refresh_token = self.cipher.decrypt(token.refresh_token_encrypted)
        new_access, new_refresh, new_ttl = self._refresh_with_provider(refresh_token)
        new_expires_at = datetime.now(timezone.utc) + new_ttl
        self.repo.upsert(
            advertiser_id=advertiser_id,
            provider=provider,
            access_token_encrypted=self.cipher.encrypt(new_access),
            refresh_token_encrypted=self.cipher.encrypt(new_refresh) if new_refresh else None,
            expires_at=new_expires_at,
            scopes=token.scopes,
        )
        return AccessToken(value=new_access, expires_at=new_expires_at)

    def _refresh_with_provider(
        self, refresh_token: str
    ) -> tuple[str, str | None, timedelta]:
        """Stand-in for ``POST /oauth/access_token``.

        Production swap-in: call Meta with ``grant_type=fb_exchange_token`` (long-
        lived tokens) or the OAuth2 refresh-token grant, parse ``access_token`` and
        ``expires_in``, return them. The rest of the service is unchanged.
        """
        # Deterministic mock: hash-derive a new access token from the refresh token.
        # Refresh tokens themselves are long-lived in Meta's model — leave unchanged.
        new_access = f"mock-access-{abs(hash(refresh_token)) % 10**12}"
        return new_access, None, _DEFAULT_TTL
