"""
Pydantic Schemas for UnitValueHistory Resource
"""
import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel, Field

# Import shared ORM config and other necessary schemas
from . import orm_config

if TYPE_CHECKING:
    from .club import ClubReadBasic # For nesting club info


class UnitValueHistoryBase(BaseModel):
    club_id: uuid.UUID
    valuation_date: date = Field(..., example="2025-04-22")
    total_club_value: Decimal = Field(..., max_digits=20, decimal_places=2, example=Decimal("150500.75"))
    total_units_outstanding: Decimal = Field(..., max_digits=25, decimal_places=8, example=Decimal("14866.54321000"))
    unit_value: Decimal = Field(..., max_digits=20, decimal_places=8, example=Decimal("10.12345678"))

# UnitValueHistory is usually calculated by a backend process, not created/updated via API
# class UnitValueHistoryCreate(UnitValueHistoryBase): ...
# class UnitValueHistoryUpdate(BaseModel): ...


class UnitValueHistoryRead(UnitValueHistoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    club: 'ClubReadBasic' # Nest basic club info
    model_config = orm_config