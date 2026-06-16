from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.advertiser import Advertiser


class AdvertiserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, advertiser: Advertiser) -> Advertiser:
        self.session.add(advertiser)
        self.session.flush()
        return advertiser

    def get(self, advertiser_id: uuid.UUID) -> Advertiser | None:
        return self.session.get(Advertiser, advertiser_id)

    def get_by_external_ref(self, external_ref: str) -> Advertiser | None:
        stmt = select(Advertiser).where(Advertiser.external_ref == external_ref)
        return self.session.scalar(stmt)
