from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversion_tag import ConversionTag


class ConversionTagRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, tag: ConversionTag) -> ConversionTag:
        self.session.add(tag)
        self.session.flush()
        return tag

    def get(self, tag_id: uuid.UUID) -> ConversionTag | None:
        return self.session.get(ConversionTag, tag_id)

    def get_by_advertiser_and_name(
        self, advertiser_id: uuid.UUID, name: str
    ) -> ConversionTag | None:
        stmt = select(ConversionTag).where(
            ConversionTag.advertiser_id == advertiser_id,
            ConversionTag.name == name,
        )
        return self.session.scalar(stmt)

    def list_for_advertiser(self, advertiser_id: uuid.UUID) -> list[ConversionTag]:
        stmt = (
            select(ConversionTag)
            .where(ConversionTag.advertiser_id == advertiser_id)
            .order_by(ConversionTag.created_at.desc())
        )
        return list(self.session.scalars(stmt))
