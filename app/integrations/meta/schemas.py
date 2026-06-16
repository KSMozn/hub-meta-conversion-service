"""Schemas exchanged with Meta. These are deliberately small and stable.

Real Meta responses include many more fields; we project to what the Hub cares
about. When we add a field we add it here and to the model layer in lockstep.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class MetaPixel(BaseModel):
    id: str
    name: str
    status: str = "ACTIVE"


class CustomConversionRuleInput(BaseModel):
    field: str
    operator: str = "eq"
    value: str


class CustomConversionCreateInput(BaseModel):
    pixel_id: str = Field(..., description="Meta pixel id (not the Hub UUID)")
    name: str
    event_type: str
    category: str
    value: Decimal | None = None
    currency: str | None = None
    rule: CustomConversionRuleInput | None = None


class CustomConversion(BaseModel):
    id: str
    pixel_id: str
    name: str
    event_type: str
    category: str
    value: Decimal | None = None
    currency: str | None = None
    rule: dict[str, Any] | None = None
