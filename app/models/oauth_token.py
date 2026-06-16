from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.advertiser import Advertiser


class OAuthToken(UUIDPKMixin, TimestampMixin, Base):
    """OAuth2 credentials per (advertiser, provider).

    Both access and refresh tokens are stored encrypted; ``TokenCipher`` round-trips
    them. The token row is the single source of truth — when the Meta client gets a
    401 it refreshes through the OAuth service, which updates this row in place.
    """

    __tablename__ = "oauth_tokens"

    advertiser_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("advertisers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    access_token_encrypted: Mapped[str] = mapped_column(String, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scopes: Mapped[str | None] = mapped_column(String, nullable=True)

    advertiser: Mapped[Advertiser] = relationship(back_populates="oauth_tokens")

    __table_args__ = (
        UniqueConstraint(
            "advertiser_id", "provider", name="uq_oauth_tokens_advertiser_id_provider"
        ),
    )
