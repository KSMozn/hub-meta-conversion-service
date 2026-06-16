from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.advertiser import Advertiser
from app.repositories.advertiser import AdvertiserRepository
from app.schemas.advertiser import AdvertiserCreate
from app.services.exceptions import ConflictError, NotFoundError


class AdvertiserService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = AdvertiserRepository(session)

    def create(self, payload: AdvertiserCreate) -> Advertiser:
        advertiser = Advertiser(
            name=payload.name,
            external_ref=payload.external_ref,
            meta_business_id=payload.meta_business_id,
            meta_ad_account_id=payload.meta_ad_account_id,
        )
        try:
            return self.repo.create(advertiser)
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError(
                f"advertiser with external_ref={payload.external_ref!r} already exists"
            ) from exc

    def get(self, advertiser_id: uuid.UUID) -> Advertiser:
        advertiser = self.repo.get(advertiser_id)
        if advertiser is None:
            raise NotFoundError(f"advertiser {advertiser_id} not found")
        return advertiser
