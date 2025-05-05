# backend/schemas/member_transaction.py

"""
Pydantic Schemas for MemberTransaction Resource
(Deposits/Withdrawals affecting units)
"""
import uuid
import logging # Import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

# Import shared ORM config and other necessary schemas/enums
from . import orm_config
from backend.models.enums import MemberTransactionType

log = logging.getLogger(__name__) # Logger for rebuild messages

if TYPE_CHECKING:
    # Use real imports for type checking
    from .user import UserReadBasic
    from .club import ClubReadBasic


class MemberTransactionBase(BaseModel):
    # user_id and club_id are derived via membership in Read schema
    # user_id: uuid.UUID
    # club_id: uuid.UUID
    membership_id: uuid.UUID # Link via membership
    transaction_type: MemberTransactionType
    transaction_date: datetime = Field(..., example="2025-04-23T09:00:00Z")
    amount: Decimal = Field(..., max_digits=15, decimal_places=2, example=Decimal("1000.00"))
    # Unit value and units transacted are calculated by the backend during creation
    unit_value_used: Optional[Decimal] = Field(None, max_digits=20, decimal_places=8, example=Decimal("10.12345678"))
    units_transacted: Optional[Decimal] = Field(None, max_digits=25, decimal_places=8, example=Decimal("98.78048780"))
    notes: Optional[str] = None


class MemberTransactionCreate(BaseModel):
    # These are needed by the service layer function
    user_id: uuid.UUID
    club_id: uuid.UUID
    transaction_type: MemberTransactionType # DEPOSIT or WITHDRAWAL
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    amount: Decimal = Field(..., max_digits=15, decimal_places=2, gt=Decimal(0)) # Must be positive
    notes: Optional[str] = None


# MemberTransactions are typically corrected, not updated via simple PUT/PATCH
# class MemberTransactionUpdate(BaseModel): ...


class MemberTransactionRead(MemberTransactionBase):
    id: uuid.UUID
    # Fields calculated on creation are now mandatory for read
    # Make them Optional just in case calculation failed, though service should handle
    unit_value_used: Optional[Decimal] = Field(None, max_digits=20, decimal_places=8)
    units_transacted: Optional[Decimal] = Field(None, max_digits=25, decimal_places=8)
    created_at: datetime
    updated_at: datetime
    # Use forward references for nested user/club info via membership
    user: 'UserReadBasic' # Accessed via membership.user
    club: 'ClubReadBasic' # Accessed via membership.club
    notes: Optional[str] = None

    model_config = orm_config

# --- Resolve Forward References ---
# Explicitly rebuild models defined in *this file* that use forward references.
log.debug("Attempting model rebuild in schemas/member_transaction.py...")
try:
    MemberTransactionRead.model_rebuild(force=True)
    log.debug("Model rebuild successful in schemas/member_transaction.py.")
except NameError as e:
     log.error(f"FAILED model rebuild in schemas/member_transaction.py (NameError): {e}. Check import order in __init__.py or dependencies.")
     # Don't raise here, let centralized rebuild try later if needed
except Exception as e:
     log.error(f"FAILED model rebuild in schemas/member_transaction.py (Other Error): {e}", exc_info=True)
     # Don't raise here

