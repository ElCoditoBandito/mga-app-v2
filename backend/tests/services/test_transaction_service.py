# backend/tests/services/test_transaction_service.py

import pytest
import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timezone, timedelta
from typing import Sequence, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

# Service functions to test
from backend.services import transaction_service
# CRUD functions - now used directly instead of mocked
from backend.crud import transaction as crud_transaction
from backend.crud import fund as crud_fund
from backend.crud import club as crud_club
from backend.crud import asset as crud_asset
from backend.crud import position as crud_position
from backend.crud import fund_split as crud_fund_split
# Models and Schemas
from backend.models import User, Club, Fund, Asset, Position, Transaction, FundSplit
from backend.models.enums import AssetType, OptionType, TransactionType, Currency
from backend.schemas import (
    TransactionCreateTrade, TransactionCreateDividendBrokerageInterest,
    TransactionCreateCashTransfer, TransactionCreateOptionLifecycle
)

# Import Auth0 mocking fixtures
from backend.tests.auth_fixtures import mock_auth0_token_verification, mock_get_current_active_user, test_user

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio

# --- Tests for process_trade_transaction ---

async def test_process_trade_buy_stock_success(db_session: AsyncSession, test_user: User):
    """ Test successful processing of a BUY_STOCK trade using actual CRUD functions. """
    # Arrange - Create a club, fund, and asset first
    club_data = {
        "name": f"Trade Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for trades",
        "bank_account_balance": Decimal("10000.00"),
        "creator_id": test_user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    fund_data = {
        "club_id": club.id,
        "name": "Trade Fund",
        "description": "Fund for trade testing",
        "brokerage_cash_balance": Decimal("10000.00"),
        "is_active": True
    }
    fund = await crud_fund.create_fund(db=db_session, fund_data=fund_data)
    await db_session.flush()
    
    asset_data = {
        "asset_type": AssetType.STOCK,
        "symbol": f"TRADE_{uuid.uuid4().hex[:6]}",
        "name": "Trade Test Stock",
        "currency": Currency.USD
    }
    asset = await crud_asset.create_asset(db=db_session, asset_data=asset_data)
    await db_session.flush()
    
    # Create trade input
    initial_fund_cash = fund.brokerage_cash_balance
    trade_qty = Decimal("50")
    trade_price = Decimal("150.00")
    trade_fees = Decimal("5.00")
    trade_in = TransactionCreateTrade(
        fund_id=fund.id,
        asset_id=asset.id,
        transaction_type=TransactionType.BUY_STOCK,
        quantity=trade_qty,
        price_per_unit=trade_price,
        fees_commissions=trade_fees,
        transaction_date=datetime.now(timezone.utc),
        description="Test Buy Stock"
    )
    
    # Expected calculations
    expected_gross_amount = trade_qty * trade_price
    expected_cash_effect = -(expected_gross_amount + trade_fees)
    expected_final_cash = initial_fund_cash + expected_cash_effect
    
    # Act
    result_tx = await transaction_service.process_trade_transaction(db=db_session, trade_in=trade_in)
    
    # Assert
    assert result_tx is not None
    assert result_tx.fund_id == fund.id
    assert result_tx.asset_id == asset.id
    assert result_tx.transaction_type == TransactionType.BUY_STOCK
    assert result_tx.quantity == trade_qty
    assert result_tx.price_per_unit == trade_price
    assert result_tx.total_amount == expected_gross_amount
    assert result_tx.fees_commissions == trade_fees
    
    # Verify fund cash balance was updated
    await db_session.refresh(fund)
    assert fund.brokerage_cash_balance == expected_final_cash
    
    # Verify position was created
    position = await crud_position.get_position_by_fund_and_asset(
        db=db_session,
        fund_id=fund.id,
        asset_id=asset.id
    )
    assert position is not None
    assert position.quantity == trade_qty
    assert position.average_cost_basis == trade_price # Use correct model attribute name


async def test_process_trade_buy_insufficient_funds(db_session: AsyncSession, test_user: User):
    """ Test buying stock fails with 400 if fund cash is insufficient using actual CRUD functions. """
    # Arrange - Create a club, fund, and asset first
    club_data = {
        "name": f"Low Cash Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for insufficient funds",
        "bank_account_balance": Decimal("1000.00"),
        "creator_id": test_user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    fund_data = {
        "club_id": club.id,
        "name": "Low Cash Fund",
        "description": "Fund with low cash",
        "brokerage_cash_balance": Decimal("1000.00"),  # Low cash
        "is_active": True
    }
    fund = await crud_fund.create_fund(db=db_session, fund_data=fund_data)
    await db_session.flush()
    
    asset_data = {
        "asset_type": AssetType.STOCK,
        "symbol": f"EXPENSIVE_{uuid.uuid4().hex[:6]}",
        "name": "Expensive Stock",
        "currency": Currency.USD
    }
    asset = await crud_asset.create_asset(db=db_session, asset_data=asset_data)
    await db_session.flush()
    
    # Create trade input that requires more cash than available
    trade_qty = Decimal("50")
    trade_price = Decimal("150.00")  # Cost = 7500
    trade_fees = Decimal("5.00")     # Total needed = 7505
    trade_in = TransactionCreateTrade(
        fund_id=fund.id,
        asset_id=asset.id,
        transaction_type=TransactionType.BUY_STOCK,
        quantity=trade_qty,
        price_per_unit=trade_price,
        fees_commissions=trade_fees,
        transaction_date=datetime.now(timezone.utc)
    )
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await transaction_service.process_trade_transaction(db=db_session, trade_in=trade_in)
    
    assert exc_info.value.status_code == 400
    assert "Insufficient funds" in exc_info.value.detail
    
    # Verify fund cash balance was not changed
    await db_session.refresh(fund)
    assert fund.brokerage_cash_balance == Decimal("1000.00")


# --- Tests for process_cash_receipt_transaction ---

async def test_process_cash_receipt_dividend_success(db_session: AsyncSession, test_user: User):
    """ Test successful processing of a dividend receipt using actual CRUD functions. """
    # Arrange - Create a club, fund, and asset first
    club_data = {
        "name": f"Dividend Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for dividends",
        "bank_account_balance": Decimal("1000.00"),
        "creator_id": test_user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    fund_data = {
        "club_id": club.id,
        "name": "Dividend Fund",
        "description": "Fund for dividend testing",
        "brokerage_cash_balance": Decimal("1000.00"),
        "is_active": True
    }
    fund = await crud_fund.create_fund(db=db_session, fund_data=fund_data)
    await db_session.flush()
    
    asset_data = {
        "asset_type": AssetType.STOCK,
        "symbol": f"DIV_{uuid.uuid4().hex[:6]}",
        "name": "Dividend Stock",
        "currency": Currency.USD
    }
    asset = await crud_asset.create_asset(db=db_session, asset_data=asset_data)
    await db_session.flush()
    
    # Create dividend input
    initial_fund_cash = fund.brokerage_cash_balance
    dividend_amount = Decimal("55.25")
    receipt_in = TransactionCreateDividendBrokerageInterest(
        fund_id=fund.id,
        asset_id=asset.id,
        transaction_type=TransactionType.DIVIDEND,
        total_amount=dividend_amount,
        transaction_date=datetime.now(timezone.utc),
        description="Test Dividend"
    )
    
    expected_final_cash = initial_fund_cash + dividend_amount
    
    # Act
    result_tx = await transaction_service.process_cash_receipt_transaction(db=db_session, cash_receipt_in=receipt_in)
    
    # Assert
    assert result_tx is not None
    assert result_tx.fund_id == fund.id
    assert result_tx.asset_id == asset.id
    assert result_tx.transaction_type == TransactionType.DIVIDEND
    assert result_tx.total_amount == dividend_amount
    assert result_tx.fees_commissions == Decimal("0.00")
    
    # Verify fund cash balance was updated
    await db_session.refresh(fund)
    assert fund.brokerage_cash_balance == expected_final_cash


# --- Tests for process_cash_transfer_transaction ---

async def test_process_cash_transfer_b2b_multi_split(db_session: AsyncSession, test_user: User):
    """ Test BANK_TO_BROKERAGE transfer with multiple fund splits using actual CRUD functions. """
    # Arrange - Create a club with multiple funds and fund splits
    club_data = {
        "name": f"Transfer Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for transfers",
        "bank_account_balance": Decimal("10000.00"),
        "creator_id": test_user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    # Create two funds
    fund1_data = {
        "club_id": club.id,
        "name": "Fund 1",
        "description": "First fund",
        "brokerage_cash_balance": Decimal("1000.00"),
        "is_active": True
    }
    fund2_data = {
        "club_id": club.id,
        "name": "Fund 2",
        "description": "Second fund",
        "brokerage_cash_balance": Decimal("500.00"),
        "is_active": True
    }
    fund1 = await crud_fund.create_fund(db=db_session, fund_data=fund1_data)
    fund2 = await crud_fund.create_fund(db=db_session, fund_data=fund2_data)
    await db_session.flush()
    
    # Create fund splits
    split1_data = {
        "club_id": club.id,
        "fund_id": fund1.id,
        "split_percentage": Decimal("0.6")
    }
    split2_data = {
        "club_id": club.id,
        "fund_id": fund2.id,
        "split_percentage": Decimal("0.4")
    }
    await crud_fund_split.create_fund_split(db=db_session, fund_split_data=split1_data)
    await crud_fund_split.create_fund_split(db=db_session, fund_split_data=split2_data)
    await db_session.flush()
    
    # Create transfer input
    initial_bank_cash = club.bank_account_balance
    initial_fund1_cash = fund1.brokerage_cash_balance
    initial_fund2_cash = fund2.brokerage_cash_balance
    
    amount_to_transfer = Decimal("3000.00")
    fees = Decimal("2.00")
    
    transfer_in = TransactionCreateCashTransfer(
        transaction_type=TransactionType.BANK_TO_BROKERAGE,
        total_amount=amount_to_transfer,
        fees_commissions=fees,
        transaction_date=datetime.now(timezone.utc)
    )
    
    # Expected calculations
    split1_amount = (amount_to_transfer * Decimal("0.6")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    split2_amount = (amount_to_transfer * Decimal("0.4")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    expected_bank_final = initial_bank_cash - (amount_to_transfer + fees)
    expected_fund1_final = initial_fund1_cash + split1_amount
    expected_fund2_final = initial_fund2_cash + split2_amount
    
    # Act
    result = await transaction_service.process_cash_transfer_transaction(
        db=db_session, transfer_in=transfer_in, club_id=club.id
    )
    
    # Assert
    assert isinstance(result, list)
    assert len(result) == 2
    
    # Verify transactions were created correctly
    tx1, tx2 = result if result[0].fund_id == fund1.id else (result[1], result[0])
    
    assert tx1.fund_id == fund1.id
    assert tx1.transaction_type == TransactionType.BANK_TO_BROKERAGE
    assert tx1.total_amount == split1_amount
    assert tx1.fees_commissions == fees  # Fee applied to first tx
    
    assert tx2.fund_id == fund2.id
    assert tx2.transaction_type == TransactionType.BANK_TO_BROKERAGE
    assert tx2.total_amount == split2_amount
    assert tx2.fees_commissions == Decimal("0.00")  # Fee not applied to second
    
    # Verify balances were updated
    await db_session.refresh(club)
    await db_session.refresh(fund1)
    await db_session.refresh(fund2)
    
    assert club.bank_account_balance == expected_bank_final
    assert fund1.brokerage_cash_balance == expected_fund1_final
    assert fund2.brokerage_cash_balance == expected_fund2_final


# --- Tests for get_transaction_by_id / list_transactions ---

async def test_get_transaction_by_id_service_success(db_session: AsyncSession, test_user: User):
    """ Test retrieving a transaction by ID using actual CRUD functions. """
    # Arrange - Create a club, fund, asset, and transaction first
    club_data = {
        "name": f"Tx Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for transaction retrieval",
        "bank_account_balance": Decimal("1000.00"),
        "creator_id": test_user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    fund_data = {
        "club_id": club.id,
        "name": "Tx Fund",
        "description": "Fund for transaction testing",
        "brokerage_cash_balance": Decimal("1000.00"),
        "is_active": True
    }
    fund = await crud_fund.create_fund(db=db_session, fund_data=fund_data)
    await db_session.flush()
    
    # Create a transaction directly with CRUD
    tx_data = {
        "fund_id": fund.id,
        "transaction_type": TransactionType.BROKERAGE_INTEREST,
        "transaction_date": datetime.now(timezone.utc),
        "total_amount": Decimal("25.00"),
        "description": "Test transaction for retrieval"
    }
    tx = await crud_transaction.create_transaction(db=db_session, transaction_data=tx_data)
    await db_session.flush()
    
    # Act
    result = await transaction_service.get_transaction_by_id(db=db_session, transaction_id=tx.id)
    
    # Assert
    assert result is not None
    assert result.id == tx.id
    assert result.fund_id == fund.id
    assert result.transaction_type == TransactionType.BROKERAGE_INTEREST
    assert result.total_amount == Decimal("25.00")


async def test_list_transactions_service_passes_filters(db_session: AsyncSession, test_user: User):
    """ Test listing transactions with filters using actual CRUD functions. """
    # Arrange - Create a club, fund, asset, and multiple transactions
    club_data = {
        "name": f"List Tx Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for transaction listing",
        "bank_account_balance": Decimal("1000.00"),
        "creator_id": test_user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    fund_data = {
        "club_id": club.id,
        "name": "List Tx Fund",
        "description": "Fund for transaction listing",
        "brokerage_cash_balance": Decimal("1000.00"),
        "is_active": True
    }
    fund = await crud_fund.create_fund(db=db_session, fund_data=fund_data)
    await db_session.flush()
    
    asset_data = {
        "asset_type": AssetType.STOCK,
        "symbol": f"LIST_{uuid.uuid4().hex[:6]}",
        "name": "List Test Stock",
        "currency": Currency.USD
    }
    asset = await crud_asset.create_asset(db=db_session, asset_data=asset_data)
    await db_session.flush()
    
    # Create multiple transactions
    for i in range(3):
        tx_data = {
            "fund_id": fund.id,
            "asset_id": asset.id,
            "transaction_type": TransactionType.DIVIDEND,
            "transaction_date": datetime.now(timezone.utc) - timedelta(days=i),
            "total_amount": Decimal(f"{10 * (i+1)}.00"),
            "description": f"Test transaction {i+1}"
        }
        await crud_transaction.create_transaction(db=db_session, transaction_data=tx_data)
    await db_session.flush()
    
    # Act
    result = await transaction_service.list_transactions(
        db=db_session, club_id=club.id, fund_id=fund.id, asset_id=asset.id, skip=0, limit=10
    )
    
    # Assert
    assert len(result) == 3
    # Transactions should be ordered by date (newest first)
    assert result[0].total_amount == Decimal("10.00")
    assert result[1].total_amount == Decimal("20.00")
    assert result[2].total_amount == Decimal("30.00")
