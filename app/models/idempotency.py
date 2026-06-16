from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class IdempotencyRecord(UUIDPKMixin, TimestampMixin, Base):
    """Stores the canonical response for a given ``Idempotency-Key`` + endpoint.

    Scoped by endpoint so the same key can be safely reused across endpoints
    (clients tend to do this). ``request_hash`` lets us reject reuse-with-different-body,
    which is the most common idempotency footgun.
    """

    endpoint: Mapped[str] = mapped_column(String(128), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("endpoint", "key", name="uq_idempotency_records_endpoint_key"),
    )
