# backend/tests/services/test_transaction_service.py

import pytest
import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timezone, timedelta
from typing import Sequence, List # Added List
from unittest.mock import patch, AsyncMock, call, MagicMock # Added call, MagicMock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError # For testing error handling
from fastapi import HTTPException

# Service functions to test
from backend.services import transaction_service
# CRUD functions - Will be mocked
# Models and Schemas - For type hints and data structures
from backend.models import User, Club, Fund, Asset, Position, Transaction, FundSplit
from backend.models.enums import AssetType, OptionType, TransactionType, Currency
from backend.schemas import (
    TransactionCreateTrade, TransactionCreateDividendBrokerageInterest,
    TransactionCreateCashTransfer, TransactionCreateOptionLifecycle
)

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio

# --- Constants for Mock IDs ---
TEST_CLUB_ID = uuid.uuid4()
TEST_FUND_ID = uuid.uuid4()
TEST_FUND_ID_2 = uuid.uuid4()
TEST_ASSET_ID = uuid.uuid4()
TEST_POSITION_ID = uuid.uuid4()
TEST_TX_ID = uuid.uuid4()
TEST_USER_ID = uuid.uuid4()


# --- Tests for process_trade_transaction ---

# FIX: Added patches for AsyncSession.add and AsyncSession.flush
# FIX: Corrected order of mock arguments
@patch('sqlalchemy.ext.asyncio.AsyncSession.flush', new_callable=AsyncMock)
@patch('sqlalchemy.ext.asyncio.AsyncSession.add', autospec=True)
@patch('backend.services.transaction_service._update_or_create_position', new_callable=AsyncMock)
@patch('backend.services.transaction_service.crud_transaction.create_transaction', new_callable=AsyncMock)
@patch('backend.services.transaction_service.crud_asset.get_asset', new_callable=AsyncMock)
@patch('backend.services.transaction_service.crud_fund.get_fund', new_callable=AsyncMock)
async def test_process_trade_buy_stock_success(
    mock_get_fund: AsyncMock,
    mock_get_asset: AsyncMock,
    mock_create_tx: AsyncMock,
    mock_update_pos: AsyncMock, # Mock for the helper
    mock_add: MagicMock,      # Mock for session.add
    mock_flush: AsyncMock,    # Mock for session.flush
    db_session: AsyncSession  # Still pass db_session
):
    """ Test successful processing of a BUY_STOCK trade (mocked). """
    # Arrange
    initial_fund_cash = Decimal("10000.00")
    trade_qty = Decimal("50")
    trade_price = Decimal("150.00")
    trade_fees = Decimal("5.00")
    trade_in = TransactionCreateTrade(
        fund_id=TEST_FUND_ID, asset_id=TEST_ASSET_ID, transaction_type=TransactionType.BUY_STOCK,
        quantity=trade_qty, price_per_unit=trade_price, fees_commissions=trade_fees,
        transaction_date=datetime.now(timezone.utc), description="Test Buy Mocked"
    )

    # Mock Fund returned by get_fund
    mock_fund = MagicMock(spec=Fund)
    mock_fund.id = TEST_FUND_ID
    mock_fund.brokerage_cash_balance = initial_fund_cash # Initialize balance
    mock_fund.club_id = TEST_CLUB_ID
    mock_get_fund.return_value = mock_fund

    # Mock Asset returned by get_asset
    mock_asset = MagicMock(spec=Asset)
    mock_asset.id = TEST_ASSET_ID
    mock_asset.symbol = "MOCK"
    mock_get_asset.return_value = mock_asset

    # Mock Transaction returned by create_transaction
    mock_tx = MagicMock(spec=Transaction)
    mock_tx.id = TEST_TX_ID
    mock_create_tx.return_value = mock_tx

    # Mock Position returned by the helper _update_or_create_position
    mock_pos = MagicMock(spec=Position)
    mock_pos.id = TEST_POSITION_ID
    mock_update_pos.return_value = mock_pos

    # Expected calculations
    expected_gross_amount = trade_qty * trade_price
    expected_cash_effect = -(expected_gross_amount + trade_fees)
    expected_final_cash = initial_fund_cash + expected_cash_effect

    # Act
    result_tx = await transaction_service.process_trade_transaction(db=db_session, trade_in=trade_in)

    # Assert
    mock_get_fund.assert_called_once_with(db=db_session, fund_id=TEST_FUND_ID)
    mock_get_asset.assert_called_once_with(db=db_session, asset_id=TEST_ASSET_ID)
    # Assert create_transaction was called with correct data
    mock_create_tx.assert_called_once()
    call_args_create, call_kwargs_create = mock_create_tx.call_args
    assert call_kwargs_create['transaction_data']['fund_id'] == TEST_FUND_ID
    assert call_kwargs_create['transaction_data']['asset_id'] == TEST_ASSET_ID
    assert call_kwargs_create['transaction_data']['transaction_type'] == TransactionType.BUY_STOCK
    assert call_kwargs_create['transaction_data']['quantity'] == trade_qty
    assert call_kwargs_create['transaction_data']['price_per_unit'] == trade_price
    assert call_kwargs_create['transaction_data']['total_amount'] == expected_gross_amount
    assert call_kwargs_create['transaction_data']['fees_commissions'] == trade_fees
    # Assert _update_or_create_position helper was called correctly
    mock_update_pos.assert_called_once_with(
        db=db_session,
        fund_id=TEST_FUND_ID,
        asset_id=TEST_ASSET_ID,
        quantity_change=trade_qty, # Positive for buy
        price_per_unit=trade_price
    )
    # Assert fund cash balance was updated correctly (by checking the mock object's state)
    assert mock_fund.brokerage_cash_balance == expected_final_cash
    # Assert session methods were called
    mock_add.assert_any_call(db_session, mock_fund) # Check add was called with mock_fund
    mock_flush.assert_called_once() # Check flush was called
    # Assert the service returned the transaction object from the mock
    assert result_tx == mock_tx

# FIX: Added mock for crud_asset.get_asset
@patch('backend.services.transaction_service.crud_asset.get_asset', new_callable=AsyncMock)
@patch('backend.services.transaction_service.crud_fund.get_fund', new_callable=AsyncMock)
async def test_process_trade_buy_insufficient_funds(
    mock_get_fund: AsyncMock,
    mock_get_asset: AsyncMock, # Added mock argument
    db_session: AsyncSession
):
    """ Test buying stock fails with 400 if mocked fund cash is insufficient. """
    # Arrange
    initial_fund_cash = Decimal("1000.00") # Low cash
    trade_qty = Decimal("50")
    trade_price = Decimal("150.00") # Cost = 7500
    trade_fees = Decimal("5.00") # Total needed = 7505
    trade_in = TransactionCreateTrade(
        fund_id=TEST_FUND_ID, asset_id=TEST_ASSET_ID, transaction_type=TransactionType.BUY_STOCK,
        quantity=trade_qty, price_per_unit=trade_price, fees_commissions=trade_fees,
        transaction_date=datetime.now(timezone.utc)
    )
    # Mock Fund with insufficient cash
    mock_fund = Fund(id=TEST_FUND_ID, brokerage_cash_balance=initial_fund_cash)
    mock_get_fund.return_value = mock_fund
    # *** FIX: Mock get_asset to return a valid asset ***
    # This allows the service function to proceed past the asset check
    mock_asset = Asset(id=TEST_ASSET_ID, symbol="MOCK")
    mock_get_asset.return_value = mock_asset
    # *** END FIX ***

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await transaction_service.process_trade_transaction(db=db_session, trade_in=trade_in)

    # FIX: Assert status code is 400 (Bad Request)
    assert exc_info.value.status_code == 400
    # END FIX
    assert "Insufficient funds" in exc_info.value.detail
    mock_get_fund.assert_called_once_with(db=db_session, fund_id=TEST_FUND_ID)
    # FIX: Assert get_asset was called
    mock_get_asset.assert_called_once_with(db=db_session, asset_id=TEST_ASSET_ID)
    # END FIX


# --- Tests for process_cash_receipt_transaction ---

# FIX: Added patches for AsyncSession.add and AsyncSession.flush
# FIX: Corrected order of mock arguments
@patch('sqlalchemy.ext.asyncio.AsyncSession.flush', new_callable=AsyncMock)
@patch('sqlalchemy.ext.asyncio.AsyncSession.add', autospec=True)
@patch('backend.services.transaction_service.crud_transaction.create_transaction', new_callable=AsyncMock)
@patch('backend.services.transaction_service.crud_asset.get_asset', new_callable=AsyncMock)
@patch('backend.services.transaction_service.crud_fund.get_fund', new_callable=AsyncMock)
async def test_process_cash_receipt_dividend_success(
    mock_get_fund: AsyncMock,
    mock_get_asset: AsyncMock,
    mock_create_tx: AsyncMock,
    mock_add: MagicMock,      # Mock for session.add
    mock_flush: AsyncMock,    # Mock for session.flush
    db_session: AsyncSession
):
    """ Test successful processing of a dividend receipt (mocked). """
    # Arrange
    initial_fund_cash = Decimal("1000.00")
    dividend_amount = Decimal("55.25")
    receipt_in = TransactionCreateDividendBrokerageInterest(
        fund_id=TEST_FUND_ID, asset_id=TEST_ASSET_ID, # Asset ID is required
        transaction_type=TransactionType.DIVIDEND, total_amount=dividend_amount,
        transaction_date=datetime.now(timezone.utc), description="Test Dividend Mocked"
    )

    mock_fund = MagicMock(spec=Fund)
    mock_fund.id = TEST_FUND_ID
    mock_fund.brokerage_cash_balance = initial_fund_cash # Initialize balance
    mock_get_fund.return_value = mock_fund

    mock_asset = MagicMock(spec=Asset)
    mock_asset.id = TEST_ASSET_ID
    mock_get_asset.return_value = mock_asset

    mock_tx = MagicMock(spec=Transaction)
    mock_tx.id = TEST_TX_ID
    mock_create_tx.return_value = mock_tx

    expected_final_cash = initial_fund_cash + dividend_amount
    expected_tx_data = {
        "fund_id": TEST_FUND_ID, "asset_id": TEST_ASSET_ID, "transaction_type": TransactionType.DIVIDEND,
        "transaction_date": receipt_in.transaction_date, "quantity": None, "price_per_unit": None,
        "total_amount": dividend_amount, "fees_commissions": Decimal("0.00"), "description": receipt_in.description,
    }

    # Act
    result_tx = await transaction_service.process_cash_receipt_transaction(db=db_session, cash_receipt_in=receipt_in)

    # Assert
    mock_get_fund.assert_called_once_with(db=db_session, fund_id=TEST_FUND_ID)
    mock_get_asset.assert_called_once_with(db=db_session, asset_id=TEST_ASSET_ID)
    mock_create_tx.assert_called_once_with(db=db_session, transaction_data=expected_tx_data)
    assert mock_fund.brokerage_cash_balance == expected_final_cash
    # Assert session methods were called
    mock_add.assert_any_call(db_session, mock_fund) # Check add was called with mock_fund
    mock_flush.assert_called_once() # Check flush was called
    assert result_tx == mock_tx


# --- Tests for process_cash_transfer_transaction ---

# FIX: Added patches for AsyncSession.add and AsyncSession.flush
# FIX: Corrected order of mock arguments
@patch('sqlalchemy.ext.asyncio.AsyncSession.flush', new_callable=AsyncMock)
@patch('sqlalchemy.ext.asyncio.AsyncSession.add', autospec=True)
@patch('backend.services.transaction_service.crud_transaction.create_transaction', new_callable=AsyncMock)
@patch('backend.services.transaction_service.crud_fund_split.get_fund_splits_by_club', new_callable=AsyncMock)
@patch('backend.services.transaction_service.crud_fund.get_fund', new_callable=AsyncMock) # Mock fund lookup for targets
@patch('backend.services.transaction_service.crud_club.get_club', new_callable=AsyncMock)
async def test_process_cash_transfer_b2b_multi_split(
    mock_get_club: AsyncMock,
    mock_get_fund: AsyncMock, # Will be called multiple times for target funds
    mock_get_splits: AsyncMock,
    mock_create_tx: AsyncMock,
    mock_add: MagicMock,      # Mock for session.add
    mock_flush: AsyncMock,    # Mock for session.flush
    db_session: AsyncSession
):
    """ Test BANK_TO_BROKERAGE transfer with multiple fund splits (mocked). """
    # Arrange
    initial_bank_cash = Decimal("10000.00")
    amount_to_transfer = Decimal("3000.00")
    fees = Decimal("2.00") # Fee applied to the total transfer from bank

    transfer_in = TransactionCreateCashTransfer(
        transaction_type=TransactionType.BANK_TO_BROKERAGE,
        total_amount=amount_to_transfer,
        fees_commissions=fees,
        transaction_date=datetime.now(timezone.utc)
        # fund_id/target_fund_id not relevant for B2B input schema
    )

    # Mock Club
    mock_club = MagicMock(spec=Club)
    mock_club.id = TEST_CLUB_ID
    mock_club.bank_account_balance = initial_bank_cash # Initialize balance
    mock_get_club.return_value = mock_club

    # Mock Fund Splits
    mock_split1 = FundSplit(id=uuid.uuid4(), club_id=TEST_CLUB_ID, fund_id=TEST_FUND_ID, split_percentage=Decimal("0.6"))
    mock_split2 = FundSplit(id=uuid.uuid4(), club_id=TEST_CLUB_ID, fund_id=TEST_FUND_ID_2, split_percentage=Decimal("0.4"))
    mock_get_splits.return_value = [mock_split1, mock_split2]

    # Mock Target Funds (returned by get_fund when looked up by ID from split)
    mock_fund1 = MagicMock(spec=Fund); mock_fund1.id = TEST_FUND_ID; mock_fund1.brokerage_cash_balance = Decimal("1000"); mock_fund1.club_id = TEST_CLUB_ID; mock_fund1.name="Fund 1"
    mock_fund2 = MagicMock(spec=Fund); mock_fund2.id = TEST_FUND_ID_2; mock_fund2.brokerage_cash_balance = Decimal("500"); mock_fund2.club_id = TEST_CLUB_ID; mock_fund2.name="Fund 2"
    mock_get_fund.side_effect = lambda db, fund_id: mock_fund1 if fund_id == TEST_FUND_ID else mock_fund2 if fund_id == TEST_FUND_ID_2 else None

    # Mock created transactions (service should create one per split)
    mock_tx1 = MagicMock(spec=Transaction); mock_tx1.id = uuid.uuid4()
    mock_tx2 = MagicMock(spec=Transaction); mock_tx2.id = uuid.uuid4()
    mock_create_tx.side_effect = [mock_tx1, mock_tx2] # Return in order called

    # Expected Calculations
    split1_amount = (amount_to_transfer * Decimal("0.6")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    split2_amount = (amount_to_transfer * Decimal("0.4")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    expected_bank_final = initial_bank_cash - (amount_to_transfer + fees)
    expected_fund1_final = mock_fund1.brokerage_cash_balance + split1_amount
    expected_fund2_final = mock_fund2.brokerage_cash_balance + split2_amount

    # Act
    result = await transaction_service.process_cash_transfer_transaction(
        db=db_session, transfer_in=transfer_in, club_id=TEST_CLUB_ID
    )

    # Assert
    mock_get_club.assert_called_once_with(db=db_session, club_id=TEST_CLUB_ID)
    mock_get_splits.assert_called_once_with(db=db_session, club_id=TEST_CLUB_ID)
    assert mock_get_fund.call_count == 2 # Called for each target fund
    assert mock_create_tx.call_count == 2 # One tx created per split

    # Assert create_transaction call args (check the data passed for each split)
    tx1_call_args, tx1_call_kwargs = mock_create_tx.call_args_list[0]
    assert tx1_call_kwargs['transaction_data']['fund_id'] == TEST_FUND_ID
    assert tx1_call_kwargs['transaction_data']['total_amount'] == split1_amount
    assert tx1_call_kwargs['transaction_data']['fees_commissions'] == fees # Fee applied to first tx

    tx2_call_args, tx2_call_kwargs = mock_create_tx.call_args_list[1]
    assert tx2_call_kwargs['transaction_data']['fund_id'] == TEST_FUND_ID_2
    assert tx2_call_kwargs['transaction_data']['total_amount'] == split2_amount
    assert tx2_call_kwargs['transaction_data']['fees_commissions'] == Decimal("0.00") # Fee not applied to second

    # Assert final balances on mocked objects
    assert mock_club.bank_account_balance == expected_bank_final
    assert mock_fund1.brokerage_cash_balance == expected_fund1_final
    assert mock_fund2.brokerage_cash_balance == expected_fund2_final

    # Assert session methods were called
    # Should be called for club, fund1, fund2
    assert mock_add.call_count == 3
    mock_add.assert_any_call(db_session, mock_club)
    mock_add.assert_any_call(db_session, mock_fund1)
    mock_add.assert_any_call(db_session, mock_fund2)
    mock_flush.assert_called_once() # Flush at the end

    # Assert return value
    assert isinstance(result, list)
    assert len(result) == 2
    assert result == [mock_tx1, mock_tx2]


# --- Tests for get_transaction_by_id / list_transactions --- (Mocked Example)

@patch('backend.services.transaction_service.crud_transaction.get_transaction', new_callable=AsyncMock)
async def test_get_transaction_by_id_service_success(mock_get_tx: AsyncMock, db_session: AsyncSession):
    # Arrange
    tx_id = uuid.uuid4()
    expected_tx = Transaction(id=tx_id, transaction_type=TransactionType.BUY_STOCK)
    mock_get_tx.return_value = expected_tx
    # Act
    result = await transaction_service.get_transaction_by_id(db=db_session, transaction_id=tx_id)
    # Assert
    mock_get_tx.assert_called_once_with(db=db_session, transaction_id=tx_id)
    assert result == expected_tx

@patch('backend.services.transaction_service.crud_transaction.get_multi_transactions', new_callable=AsyncMock)
async def test_list_transactions_service_passes_filters(mock_list_tx: AsyncMock, db_session: AsyncSession):
    # Arrange
    club_id = TEST_CLUB_ID
    fund_id = TEST_FUND_ID
    asset_id = TEST_ASSET_ID
    skip, limit = 10, 50
    mock_list_tx.return_value = [] # Return value doesn't matter much here
    # Act
    await transaction_service.list_transactions(
        db=db_session, club_id=club_id, fund_id=fund_id, asset_id=asset_id, skip=skip, limit=limit
    )
    # Assert: Verify CRUD was called with all correct arguments, including club_id
    mock_list_tx.assert_called_once_with(
        db=db_session, club_id=club_id, fund_id=fund_id, asset_id=asset_id, skip=skip, limit=limit
    )

# Add more tests for other transaction types and failure cases...

