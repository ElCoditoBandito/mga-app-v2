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
    from .user import UserReadBasic # Keep UserReadBasic if needed elsewhere
    from .club import ClubReadBasic # Keep ClubReadBasic if needed elsewhere
    from .club import ClubMembershipRead # Import the required nested schema


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


class MemberTransactionReadBasic(BaseModel):
    id: uuid.UUID
    membership_id: uuid.UUID = Field(..., description="Identifier for the associated club membership")
    transaction_type: MemberTransactionType = Field(..., description="Type of transaction (Deposit, Withdrawal)")
    transaction_date: datetime = Field(..., description="Date and time the transaction occurred")
    amount: Decimal = Field(..., max_digits=15, decimal_places=2, description="Cash amount deposited or withdrawn")
    notes: Optional[str] = Field(None, description="Optional notes for the transaction")
    created_at: datetime
    updated_at: datetime

    model_config = orm_config


class MemberTransactionRead(MemberTransactionBase):
    id: uuid.UUID
    # Fields calculated on creation are now mandatory for read
    # Make them Optional just in case calculation failed, though service should handle
    unit_value_used: Optional[Decimal] = Field(None, max_digits=20, decimal_places=8)
    units_transacted: Optional[Decimal] = Field(None, max_digits=25, decimal_places=8)
    created_at: datetime
    updated_at: datetime
    # Use forward references for nested user/club info via membership
    membership: 'ClubMembershipRead' # Expect nested membership object
    notes: Optional[str] = None

    model_config = orm_config

