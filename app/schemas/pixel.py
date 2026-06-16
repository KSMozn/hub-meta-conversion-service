from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PixelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    advertiser_id: uuid.UUID
    meta_pixel_id: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime


class PixelSyncRequest(BaseModel):
    advertiser_id: uuid.UUID = Field(..., description="Hub advertiser to sync pixels for")


class PixelSyncResult(BaseModel):
    advertiser_id: uuid.UUID
    pixels_fetched: int
    pixels_created: int
    pixels_updated: int
    pixels: list[PixelOut]
