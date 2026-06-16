from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.conversion_tag import ConversionTag
    from app.models.oauth_token import OAuthToken
    from app.models.pixel import Pixel


class Advertiser(UUIDPKMixin, TimestampMixin, Base):
    """An advertiser the Hub manages on behalf of an internal client.

    ``external_ref`` is the upstream client's identifier (e.g. CRM account id);
    the Hub treats it as opaque but unique.
    """

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    meta_business_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meta_ad_account_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    pixels: Mapped[list[Pixel]] = relationship(
        back_populates="advertiser",
        cascade="all, delete-orphan",
    )
    conversion_tags: Mapped[list[ConversionTag]] = relationship(
        back_populates="advertiser",
        cascade="all, delete-orphan",
    )
    oauth_tokens: Mapped[list[OAuthToken]] = relationship(
        back_populates="advertiser",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("external_ref", name="uq_advertisers_external_ref"),
    )
