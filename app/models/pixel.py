from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.advertiser import Advertiser
    from app.models.conversion_tag import ConversionTag


class Pixel(UUIDPKMixin, TimestampMixin, Base):
    """A Meta Pixel registered against one of our advertisers.

    ``meta_pixel_id`` is unique per Meta account; we enforce uniqueness inside
    the Hub too so re-syncs are idempotent.
    """

    advertiser_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("advertisers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    meta_pixel_id: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")

    advertiser: Mapped[Advertiser] = relationship(back_populates="pixels")
    conversion_tags: Mapped[list[ConversionTag]] = relationship(
        back_populates="pixel",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("meta_pixel_id", name="uq_pixels_meta_pixel_id"),
    )
