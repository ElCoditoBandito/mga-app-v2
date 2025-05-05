# backend/schemas/reporting.py

"""
Pydantic Schemas for Reporting Responses
"""
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

# Import shared ORM config and other necessary schemas/enums
from . import orm_config # Assuming orm_config is defined in schemas/__init__.py

if TYPE_CHECKING:
    # Import schemas used within these reporting models
    from .member_transaction import MemberTransactionRead
    # Add other imports if needed by future reporting schemas


# --- Pydantic Model for Member Statement Response ---
class MemberStatementData(BaseModel):
    club_id: uuid.UUID
    user_id: uuid.UUID
    membership_id: uuid.UUID
    statement_date: date = Field(default_factory=date.today)
    current_unit_balance: Decimal = Field(..., max_digits=25, decimal_places=8)
    latest_unit_value: Optional[Decimal] = Field(None, max_digits=20, decimal_places=8)
    current_equity_value: Decimal = Field(..., max_digits=15, decimal_places=2)
    # Use forward reference if MemberTransactionRead isn't imported directly above
    transactions: List['MemberTransactionRead'] = []
    # No model_config = orm_config needed here as it's not directly mapping an ORM model


# --- Pydantic Model for Club Performance Response ---
class ClubPerformanceData(BaseModel):
    club_id: uuid.UUID
    start_date: date
    end_date: date
    start_unit_value: Optional[Decimal] = Field(None, max_digits=20, decimal_places=8)
    end_unit_value: Optional[Decimal] = Field(None, max_digits=20, decimal_places=8)
    holding_period_return: Optional[float] = Field(None, description="Simple return as a decimal (e.g., 0.10 for 10%)")
    # No model_config = orm_config needed here


# --- Resolve Forward References ---
# Call model_rebuild here for schemas defined in *this* file that use forward refs
# (Only MemberStatementData uses one here)
try:
    MemberStatementData.model_rebuild(force=True)
    # ClubPerformanceData has no forward refs, no rebuild needed
except NameError as e:
     print(f"Warning: Failed to rebuild forward refs in schemas/reporting.py: {e}.")
except Exception as e:
     print(f"Warning: Unexpected error rebuilding forward refs in schemas/reporting.py: {e}")

