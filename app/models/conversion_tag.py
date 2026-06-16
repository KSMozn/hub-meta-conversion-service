from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from decimal import Decimal

    from app.models.advertiser import Advertiser
    from app.models.pixel import Pixel


class ConversionTag(UUIDPKMixin, TimestampMixin, Base):
    """Meta "custom conversion" / conversion tag we own on behalf of an advertiser.

    ``meta_custom_conversion_id`` is null until the row is reconciled with Meta,
    so callers can read back rows that are mid-creation. ``payload`` holds the
    last request we sent to Meta — useful for replay and audits.
    """

    advertiser_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("advertisers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pixel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pixels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    rule: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    meta_custom_conversion_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")

    advertiser: Mapped[Advertiser] = relationship(back_populates="conversion_tags")
    pixel: Mapped[Pixel] = relationship(back_populates="conversion_tags")

    __table_args__ = (
        UniqueConstraint(
            "advertiser_id", "name", name="uq_conversion_tags_advertiser_id_name"
        ),
    )
