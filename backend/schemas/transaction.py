"""
Pydantic Schemas for Transaction Resource
"""
# backend/schemas/transaction.py (Corrected - Applying fund_id fix to original)

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal, Any, TYPE_CHECKING

# Use model_validator for Pydantic v2
from pydantic import BaseModel, Field, model_validator, ConfigDict
from pydantic_core import PydanticCustomError

# Import shared ORM config and other necessary schemas/enums
# Assuming orm_config exists or replace with model_config directly
# from . import orm_config
# Make sure this reflects your updated enums.py
from backend.models.enums import TransactionType

if TYPE_CHECKING:
    # Define dummy classes if schemas aren't available during type checking phase
    # This prevents import errors in linters/type checkers
    from .asset import AssetReadBasic
    from .fund import FundReadBasic


class TransactionBase(BaseModel):
    """ Base schema for reading transaction data """
    # fund_id is Optional as defined in original
    fund_id: Optional[uuid.UUID] = None # Nullable for club-level transactions
    asset_id: Optional[uuid.UUID] = None # Nullable for cash-only transactions
    transaction_type: TransactionType
    transaction_date: datetime = Field(..., example="2025-04-23T10:00:00Z")
    quantity: Optional[Decimal] = Field(None, max_digits=18, decimal_places=6, example=Decimal("10.00"))
    price_per_unit: Optional[Decimal] = Field(None, max_digits=15, decimal_places=4, example=Decimal("175.50"))
    total_amount: Optional[Decimal] = Field(None, max_digits=15, decimal_places=2, example=Decimal("1755.00")) # Gross amount, expense amount, transfer amount etc.
    fees_commissions: Decimal = Field(Decimal("0.00"), max_digits=10, decimal_places=2, example=Decimal("1.99"))
    description: Optional[str] = Field(None, example="Bought 10 shares AAPL")
    related_transaction_id: Optional[uuid.UUID] = None
    reverses_transaction_id: Optional[uuid.UUID] = None

    # Use Pydantic v2 config directly
    model_config = ConfigDict(
        from_attributes=True # Enable ORM mode
    )

    # Keep the original complex validator from your file
    @model_validator(mode='before')
    @classmethod
    def check_asset_id_and_fund_id_requirements(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data # Let standard validation handle non-dict types

        tx_type_str = data.get('transaction_type')
        asset_id = data.get('asset_id')
        fund_id = data.get('fund_id') # Check fund_id presence now too

        # Ensure tx_type exists and is a valid enum member before proceeding
        try:
            tx_type = TransactionType(tx_type_str) if tx_type_str else None
        except ValueError:
            tx_type = None # Let standard field validation catch invalid enum later

        if tx_type: # Only validate if tx_type is recognizable
            # --- Asset ID Checks ---
            asset_required_types = {
                TransactionType.BUY_STOCK, TransactionType.SELL_STOCK, TransactionType.DIVIDEND, # Dividend needs asset
                TransactionType.BUY_OPTION, TransactionType.SELL_OPTION, TransactionType.CLOSE_OPTION_BUY,
                TransactionType.CLOSE_OPTION_SELL, TransactionType.OPTION_EXPIRATION, TransactionType.OPTION_EXERCISE,
                TransactionType.OPTION_ASSIGNMENT #, TransactionType.INTERFUND_POSITION_TRANSFER # Uncomment if this type exists
            }
            # Types where asset_id MUST be null (usually cash-only or club level)
            asset_forbidden_types = {
                TransactionType.CLUB_EXPENSE, TransactionType.BANK_TO_BROKERAGE, TransactionType.BROKERAGE_TO_BANK,
                TransactionType.INTERFUND_CASH_TRANSFER,
                TransactionType.BANK_INTEREST, TransactionType.BROKERAGE_INTEREST # Assuming interest is on cash balance
                # Adjustment, Reversal can optionally have asset_id
            }

            if tx_type in asset_required_types and not asset_id:
                raise PydanticCustomError(
                    'value_error', "Field 'asset_id' is required for transaction type '{tx_type}'", {'tx_type': tx_type.value}
                )
            if tx_type in asset_forbidden_types and asset_id:
                raise PydanticCustomError(
                     'value_error', "Field 'asset_id' must be null for transaction type '{tx_type}'", {'tx_type': tx_type.value}
                )

            # --- Fund ID Checks ---
            # Types that MUST belong to a fund (fund_id is required)
            fund_required_types = {
                TransactionType.BUY_STOCK, TransactionType.SELL_STOCK,
                TransactionType.BUY_OPTION, TransactionType.SELL_OPTION, TransactionType.CLOSE_OPTION_BUY,
                TransactionType.CLOSE_OPTION_SELL, TransactionType.OPTION_EXPIRATION, TransactionType.OPTION_EXERCISE,
                TransactionType.OPTION_ASSIGNMENT, # TransactionType.INTERFUND_POSITION_TRANSFER, # Uncomment if exists
                TransactionType.INTERFUND_CASH_TRANSFER, # Requires source fund_id
                TransactionType.BROKERAGE_TO_BANK, # Requires source fund_id
                TransactionType.BANK_TO_BROKERAGE, # Requires target fund_id (should be present)
                TransactionType.BROKERAGE_INTEREST, # Interest earned in a specific fund's brokerage
                TransactionType.DIVIDEND # Dividend received into a specific fund's brokerage
                # Adjustment, Reversal might apply to a fund or be club-level
            }
             # Types that MUST be club-level (fund_id must be null)
            fund_forbidden_types = {
                 TransactionType.CLUB_EXPENSE,
                 TransactionType.BANK_INTEREST
             }

            if tx_type in fund_required_types and not fund_id:
                 raise PydanticCustomError(
                     'value_error', "Field 'fund_id' is required for transaction type '{tx_type}'", {'tx_type': tx_type.value}
                 )
            if tx_type in fund_forbidden_types and fund_id:
                 raise PydanticCustomError(
                      'value_error', "Field 'fund_id' must be null for transaction type '{tx_type}'", {'tx_type': tx_type.value}
                 )
            # Note: For Adjustment/Reversal, fund_id might be optional - logic doesn't forbid/require here.

        return data


# --- Specific Create Schemas ---

class TransactionCreateBase(BaseModel):
    """ Base schema for creating transactions - common fields """
    # **FIX:** Add fund_id here, make it optional in base, specific types might require it via validators
    fund_id: Optional[uuid.UUID] = None
    asset_id: Optional[uuid.UUID] = None # Optional here, specific types can require it
    transaction_type: TransactionType
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None
    fees_commissions: Decimal = Field(Decimal("0.00"), max_digits=10, decimal_places=2)
    # total_amount, quantity, price_per_unit are specific to transaction types


class TransactionCreateTrade(TransactionCreateBase):
    """ Schema for creating trade transactions (buy/sell stock/option) """
    # fund_id inherited, required check done in TransactionBase validator
    # asset_id inherited, required check done in TransactionBase validator
    quantity: Decimal = Field(..., gt=Decimal(0), max_digits=18, decimal_places=6, description="Number of shares/contracts")
    price_per_unit: Decimal = Field(..., ge=Decimal(0), max_digits=15, decimal_places=4)

    # Keep original validator for type check
    @model_validator(mode='before')
    @classmethod
    def check_trade_type(cls, data: Any) -> Any:
        if not isinstance(data, dict): return data
        tx_type = data.get('transaction_type')
        valid_types = { tt.value for tt in [TransactionType.BUY_STOCK, TransactionType.SELL_STOCK, TransactionType.BUY_OPTION, TransactionType.SELL_OPTION, TransactionType.CLOSE_OPTION_BUY, TransactionType.CLOSE_OPTION_SELL] }
        if tx_type not in valid_types: raise PydanticCustomError('value_error', "Invalid transaction_type '{tx_type}' for Trade", {'tx_type': tx_type})
        return data


class TransactionCreateDividendBrokerageInterest(TransactionCreateBase):
    """ Schema for creating dividend or brokerage interest transactions """
    # fund_id inherited, required check done in TransactionBase validator
    # asset_id inherited, requirement checked in TransactionBase validator
    total_amount: Decimal = Field(..., gt=Decimal(0), max_digits=15, decimal_places=2, description="Gross amount received")

    # Keep original validator for type check
    @model_validator(mode='before')
    @classmethod
    def check_dividend_brokerage_interest_type(cls, data: Any) -> Any:
        if not isinstance(data, dict): return data
        tx_type = data.get('transaction_type')
        valid_types = {TransactionType.DIVIDEND.value, TransactionType.BROKERAGE_INTEREST.value}
        if tx_type not in valid_types:
             raise PydanticCustomError('value_error', "Invalid transaction_type '{tx_type}' for Dividend/Brokerage Interest", {'tx_type': tx_type})
        # Specific asset_id checks are now handled in TransactionBase validator
        return data


class TransactionCreateBankInterest(TransactionCreateBase):
    """ Schema for creating bank interest transactions """
    # fund_id must be null (checked by base validator)
    # asset_id must be null (checked by base validator)
    transaction_type: Literal[TransactionType.BANK_INTEREST] = Field(TransactionType.BANK_INTEREST)
    total_amount: Decimal = Field(..., gt=Decimal(0), max_digits=15, decimal_places=2) # The cash amount received


class TransactionCreateClubExpense(TransactionCreateBase):
    """ Schema for creating club expense transactions """
    # fund_id must be null (checked by base validator)
    # asset_id must be null (checked by base validator)
    transaction_type: Literal[TransactionType.CLUB_EXPENSE] = Field(TransactionType.CLUB_EXPENSE)
    total_amount: Decimal = Field(..., gt=Decimal(0), max_digits=15, decimal_places=2) # Amount of the expense


class TransactionCreateCashTransfer(TransactionCreateBase):
    """ Schema for creating cash transfer transactions """
    # fund_id inherited (source or target depending on type), requirement checked in TransactionBase validator
    target_fund_id: Optional[uuid.UUID] = None # Required for INTERFUND_CASH_TRANSFER
    total_amount: Decimal = Field(..., gt=Decimal(0), max_digits=15, decimal_places=2) # Amount transferred

    # Keep original validator for type check and target_fund_id logic
    @model_validator(mode='before')
    @classmethod
    def check_cash_transfer_type(cls, data: Any) -> Any:
        if not isinstance(data, dict): return data
        tx_type = data.get('transaction_type')
        target_fund_id = data.get('target_fund_id')
        valid_types = { tt.value for tt in [TransactionType.BANK_TO_BROKERAGE, TransactionType.BROKERAGE_TO_BANK, TransactionType.INTERFUND_CASH_TRANSFER] }
        if tx_type not in valid_types: raise PydanticCustomError('value_error', "Invalid transaction_type '{tx_type}' for Cash Transfer", {'tx_type': tx_type})
        if tx_type == TransactionType.INTERFUND_CASH_TRANSFER.value and not target_fund_id: raise PydanticCustomError('value_error', "Field 'target_fund_id' is required for Interfund Cash Transfer", {})
        if tx_type != TransactionType.INTERFUND_CASH_TRANSFER.value and target_fund_id: raise PydanticCustomError('value_error', "Field 'target_fund_id' must be null unless transaction type is Interfund Cash Transfer", {})
        # Add check for fund_id == target_fund_id for interfund transfers
        if tx_type == TransactionType.INTERFUND_CASH_TRANSFER.value and data.get('fund_id') == target_fund_id and target_fund_id is not None:
            raise PydanticCustomError('value_error', "Source and target fund cannot be the same for INTERFUND_CASH_TRANSFER", {})
        return data


class TransactionCreateOptionLifecycle(TransactionCreateBase):
    """ Schema for creating option lifecycle event transactions """
    # fund_id inherited, required check done in TransactionBase validator
    # asset_id inherited, required check done in TransactionBase validator
    quantity: Decimal = Field(..., gt=Decimal(0), max_digits=18, decimal_places=6, description="Number of contracts affected")

    # Keep original validator for type check
    @model_validator(mode='before')
    @classmethod
    def check_option_lifecycle_type(cls, data: Any) -> Any:
        if not isinstance(data, dict): return data
        tx_type = data.get('transaction_type')
        valid_types = { tt.value for tt in [TransactionType.OPTION_EXPIRATION, TransactionType.OPTION_EXERCISE, TransactionType.OPTION_ASSIGNMENT] }
        if tx_type not in valid_types: raise PydanticCustomError('value_error', "Invalid transaction_type '{tx_type}' for Option Lifecycle", {'tx_type': tx_type})
        return data


class TransactionCreateAdjustmentReversal(TransactionCreateBase):
    """ Schema for creating adjustment or reversal transactions """
    # fund_id might be optional for these types (base validator allows null)
    reverses_transaction_id: Optional[uuid.UUID] = None # Required for REVERSAL
    # asset_id inherited, optional (base validator allows null)
    quantity: Optional[Decimal] = Field(None, max_digits=18, decimal_places=6)
    total_amount: Optional[Decimal] = Field(None, max_digits=15, decimal_places=2)
    description: str = Field(..., min_length=1) # Required for these types

    # Keep original validator for type check and reverses_transaction_id logic
    @model_validator(mode='before')
    @classmethod
    def check_adj_rev_type(cls, data: Any) -> Any:
        if not isinstance(data, dict): return data
        tx_type = data.get('transaction_type')
        reverses_id = data.get('reverses_transaction_id')
        valid_types = {TransactionType.ADJUSTMENT.value, TransactionType.REVERSAL.value} # Assuming these exist in Enum
        if tx_type not in valid_types: raise PydanticCustomError('value_error', "Invalid transaction_type '{tx_type}' for Adjustment/Reversal", {'tx_type': tx_type})
        if tx_type == TransactionType.REVERSAL.value and not reverses_id: raise PydanticCustomError('value_error', "Field 'reverses_transaction_id' is required for Reversal transactions", {})
        if tx_type == TransactionType.ADJUSTMENT.value and reverses_id: raise PydanticCustomError('value_error', "Field 'reverses_transaction_id' must be null for Adjustment transactions", {})
        return data


# --- Update Schema ---
class TransactionUpdate(BaseModel):
    """ Schema for updating a transaction (e.g., description) """
    description: Optional[str] = None
    # Add other updatable fields if necessary
    # transaction_date: Optional[datetime] = None # Be careful allowing date changes
    # fees_commissions: Optional[Decimal] = None # Be careful allowing financial changes

    model_config = ConfigDict(extra='forbid')


# --- Read Schemas ---
class TransactionReadBasic(TransactionBase):
    """ Basic read schema, inherits fields from TransactionBase """
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # Inherits fund_id, asset_id, etc. from TransactionBase
    model_config = ConfigDict(from_attributes=True)


class TransactionRead(TransactionBase):
    """ Detailed read schema, potentially including nested objects """
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # Inherits fund_id, asset_id, etc. from TransactionBase

    # Optionally include nested representations of related objects
    asset: Optional['AssetReadBasic'] = None # Example using TYPE_CHECKING block above
    fund: Optional['FundReadBasic'] = None # Example using TYPE_CHECKING block above
    # related_transaction: Optional['TransactionReadBasic'] = None # Requires model_rebuild if uncommented
    # reversed_by_transaction: Optional['TransactionReadBasic'] = None # Requires model_rebuild if uncommented

    model_config = ConfigDict(from_attributes=True)

    # Remember to call model_rebuild() in your app startup if you uncomment nested transaction refs
    # or ensure Pydantic v2 handles it automatically.


