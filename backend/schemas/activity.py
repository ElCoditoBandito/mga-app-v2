import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from backend.models.enums import TransactionType, MemberTransactionType

class ActivityFeedItem(BaseModel):
    id: uuid.UUID  # Original transaction ID
    activity_date: datetime
    item_type: str  # e.g., "ClubExpense", "MemberDeposit", "BuyStock", "MemberWithdrawal"
    description: str  # A user-friendly summary
    amount: Optional[Decimal] = None  # Net financial impact if applicable
    user_name: Optional[str] = None  # For member transactions
    asset_symbol: Optional[str] = None  # For asset-related transactions
    fund_name: Optional[str] = None  # For fund-related transactions

    model_config = {"from_attributes": True}