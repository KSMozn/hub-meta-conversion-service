from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


EventType = Literal[
    "Purchase",
    "Lead",
    "CompleteRegistration",
    "AddToCart",
    "InitiateCheckout",
    "Subscribe",
    "ViewContent",
    "Custom",
]

Category = Literal[
    "purchase",
    "lead",
    "registration",
    "add_to_cart",
    "checkout",
    "subscribe",
    "view_content",
    "other",
]


class ConversionTagRule(BaseModel):
    """A minimal subset of Meta's custom-conversion rule DSL."""

    field: str = Field(min_length=1)
    operator: Literal["eq", "neq", "contains", "i_contains"] = "eq"
    value: str


class ConversionTagCreate(BaseModel):
    pixel_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    event_type: EventType
    category: Category
    value: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    rule: ConversionTagRule | None = None

    @model_validator(mode="after")
    def _value_requires_currency(self) -> ConversionTagCreate:
        if (self.value is None) != (self.currency is None):
            raise ValueError("value and currency must be provided together")
        return self


class ConversionTagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    advertiser_id: uuid.UUID
    pixel_id: uuid.UUID
    name: str
    event_type: str
    category: str
    value: Decimal | None
    currency: str | None
    rule: dict[str, Any] | None
    meta_custom_conversion_id: str | None
    status: str
    created_at: datetime
    updated_at: datetime
