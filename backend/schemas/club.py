# backend/schemas/club.py

"""
Pydantic Schemas for Club and ClubMembership Resources
"""
import uuid
import logging # Import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel, Field, ConfigDict

# Import shared ORM config and other necessary schemas/enums
from . import orm_config
from backend.models.enums import ClubRole

log = logging.getLogger(__name__) # Logger for rebuild messages

if TYPE_CHECKING:
    # Use real imports within TYPE_CHECKING block
    from .user import UserReadBasic
    from .fund import FundReadBasic, FundSplitRead
    from .position import PositionRead
    from .unit_value import UnitValueHistoryRead
    # Ensure AssetReadBasic is imported if needed by PositionRead
    from .asset import AssetReadBasic


# --- Club Schemas ---

class ClubBase(BaseModel):
    name: str = Field(..., example="Tech Innovators Club")
    description: Optional[str] = Field(None, example="Investing in early-stage tech companies.")

class ClubCreate(ClubBase):
    pass

class ClubUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(extra='forbid')

class ClubReadBasic(ClubBase):
    id: uuid.UUID
    model_config = orm_config

class ClubRead(ClubBase):
    id: uuid.UUID
    bank_account_balance: Decimal = Field(..., max_digits=15, decimal_places=2)
    created_at: datetime
    updated_at: datetime
    memberships: List['ClubMembershipReadBasicUser'] = []
    funds: List['FundReadBasic'] = []
    fund_splits: List['FundSplitRead'] = []
    model_config = orm_config


# --- ClubMembership Schemas ---

class ClubMembershipBase(BaseModel):
    user_id: uuid.UUID
    club_id: uuid.UUID
    role: ClubRole = ClubRole.MEMBER

class ClubMembershipCreate(BaseModel):
    user_id: uuid.UUID
    club_id: uuid.UUID
    role: ClubRole = ClubRole.MEMBER

class ClubMembershipUpdate(BaseModel):
    role: Optional[ClubRole] = None
    model_config = ConfigDict(extra='forbid')

class ClubMembershipRead(ClubMembershipBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    user: 'UserReadBasic'
    club: 'ClubReadBasic'
    model_config = orm_config

class ClubMembershipReadBasicUser(ClubMembershipBase):
    id: uuid.UUID
    user: 'UserReadBasic'
    model_config = orm_config


# --- Specific Response Models ---

class ClubPortfolio(BaseModel):
    club_id: uuid.UUID
    valuation_date: date
    total_market_value: Decimal
    total_cash_value: Decimal
    aggregated_positions: List['PositionRead'] # Forward reference
    recent_unit_value: Optional['UnitValueHistoryRead'] = None # Forward reference
    model_config = orm_config

# --- Resolve Forward References ---
# Explicitly rebuild models defined in *this file* that use forward references.
log.debug("Attempting model rebuild in schemas/club.py...")
try:
    ClubRead.model_rebuild(force=True)
    ClubMembershipRead.model_rebuild(force=True)
    ClubMembershipReadBasicUser.model_rebuild(force=True)
    ClubPortfolio.model_rebuild(force=True) # Add rebuild for ClubPortfolio
    log.debug("Model rebuild successful in schemas/club.py.")
except NameError as e:
     log.error(f"FAILED model rebuild in schemas/club.py (NameError): {e}. Check import order in __init__.py or dependencies.")
     # Don't raise here, let centralized rebuild try later if needed
except Exception as e:
     log.error(f"FAILED model rebuild in schemas/club.py (Other Error): {e}", exc_info=True)
     # Don't raise here

