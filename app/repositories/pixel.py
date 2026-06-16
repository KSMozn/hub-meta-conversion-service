from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pixel import Pixel


class PixelRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_advertiser(self, advertiser_id: uuid.UUID) -> list[Pixel]:
        stmt = (
            select(Pixel)
            .where(Pixel.advertiser_id == advertiser_id)
            .order_by(Pixel.name)
        )
        return list(self.session.scalars(stmt))

    def get_by_meta_id(self, meta_pixel_id: str) -> Pixel | None:
        stmt = select(Pixel).where(Pixel.meta_pixel_id == meta_pixel_id)
        return self.session.scalar(stmt)

    def upsert_from_meta(
        self,
        *,
        advertiser_id: uuid.UUID,
        meta_pixel_id: str,
        name: str,
        status: str,
    ) -> tuple[Pixel, bool]:
        """Insert or update a pixel by ``meta_pixel_id``. Returns (pixel, created)."""
        existing = self.get_by_meta_id(meta_pixel_id)
        if existing is None:
            pixel = Pixel(
                advertiser_id=advertiser_id,
                meta_pixel_id=meta_pixel_id,
                name=name,
                status=status,
            )
            self.session.add(pixel)
            self.session.flush()
            return pixel, True

        existing.name = name
        existing.status = status
        existing.advertiser_id = advertiser_id
        self.session.flush()
        return existing, False
