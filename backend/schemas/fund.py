# backend/schemas/fund.py

"""
Pydantic Schemas for Fund and FundSplit Resources
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

# Import field_validator instead of validator for Pydantic v2
from pydantic import BaseModel, Field, ConfigDict, field_validator

# Import shared ORM config and other necessary schemas/enums
from . import orm_config

if TYPE_CHECKING:
    from .club import ClubReadBasic # For nesting basic club info
    from .position import PositionRead # For FundReadWithPositions
    # Ensure AssetReadBasic is imported if needed by PositionRead
    from .asset import AssetReadBasic


# --- Fund Schemas ---

class FundBase(BaseModel):
    club_id: uuid.UUID
    name: str = Field(..., example="Main Fund")
    description: Optional[str] = Field(None, example="Core portfolio holdings.")
    is_active: bool = True

class FundCreate(BaseModel):
    # club_id usually inferred from context
    name: str = Field(..., example="Growth Fund")
    description: Optional[str] = Field(None, example="Focus on high-growth potential assets.")

class FundUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    model_config = ConfigDict(extra='forbid')

class FundReadBasic(FundBase):
    id: uuid.UUID
    model_config = orm_config

class FundRead(FundBase):
    id: uuid.UUID
    brokerage_cash_balance: Decimal = Field(..., max_digits=15, decimal_places=2)
    created_at: datetime
    updated_at: datetime
    club: 'ClubReadBasic' # Link back to parent club
    model_config = orm_config

# Specific Read schema including positions
class FundReadWithPositions(FundRead):
    positions: List['PositionRead'] = []
    model_config = orm_config


# --- FundSplit Schemas ---

class FundSplitBase(BaseModel):
    # Removed club_id as it's implicit in the context where splits are set/read
    fund_id: uuid.UUID
    # Use Field constraints instead of redundant validator
    split_percentage: Decimal = Field(..., gt=Decimal(0), le=Decimal(1), max_digits=5, decimal_places=4, example=Decimal("0.6000"))

    # Redundant validator removed - handled by Field constraints above
    # @field_validator('split_percentage')
    # @classmethod
    # def percentage_must_be_positive_and_le_one(cls, v: Decimal) -> Decimal:
    #     # ... (validation logic) ...
    #     return v

class FundSplitCreate(FundSplitBase):
    # No longer need club_id here if it's inferred from path
    pass

class FundSplitUpdate(BaseModel):
     # Only percentage is updatable
     split_percentage: Optional[Decimal] = Field(None, gt=Decimal(0), le=Decimal(1), max_digits=5, decimal_places=4)
     model_config = ConfigDict(extra='forbid')

    #  Redundant validator removed - handled by Field constraints above
     @field_validator('split_percentage')
     @classmethod
     def percentage_must_be_positive_and_le_one(cls, v: Optional[Decimal]) -> Optional[Decimal]:
         # ... (validation logic) ...
         return v

class FundSplitRead(FundSplitBase):
    id: uuid.UUID
    club_id: uuid.UUID # Include club_id when reading
    created_at: datetime
    updated_at: datetime
    fund: Optional[FundReadBasic] = None # Optionally link back to fund
    model_config = orm_config

# --- NEW SCHEMA for Setting Multiple Splits ---
class FundSplitItem(BaseModel):
    """ Represents a single fund split item in a list for setting splits. """
    fund_id: uuid.UUID
    # Use Field constraints instead of redundant validator
    split_percentage: Decimal = Field(..., gt=Decimal(0), le=Decimal(1), max_digits=5, decimal_places=4, example=Decimal("0.6000"))

    # Redundant validator removed - handled by Field constraints above
    @field_validator('split_percentage')
    @classmethod
    def percentage_must_be_positive_and_le_one(cls, v: Decimal) -> Decimal:
        # ... (validation logic) ...
        return v
