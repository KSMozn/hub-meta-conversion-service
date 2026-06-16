from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AdvertiserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    external_ref: str = Field(min_length=1, max_length=255)
    meta_business_id: str | None = Field(default=None, max_length=64)
    meta_ad_account_id: str | None = Field(default=None, max_length=64)


class AdvertiserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    external_ref: str
    meta_business_id: str | None
    meta_ad_account_id: str | None
    created_at: datetime
    updated_at: datetime
