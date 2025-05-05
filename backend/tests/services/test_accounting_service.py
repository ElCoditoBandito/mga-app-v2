# backend/tests/services/test_accounting_service.py

import pytest
import uuid
from decimal import Decimal, ROUND_HALF_UP, DivisionByZero
from datetime import date, datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock, call, MagicMock # Import mocking utilities
from typing import List, Sequence, Optional # Added List, Sequence, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, MissingGreenlet # Added for potential use
from sqlalchemy.orm import selectinload # Import selectinload
from fastapi import HTTPException

# Service functions to test
from backend.services import accounting_service
# Import the response models defined within the service file
# from backend.services.reporting_service import MemberStatementData, ClubPerformanceData # Not needed here
# CRUD functions for verification and setup
from backend.crud import (
    user as crud_user,
    club as crud_club,
    club_membership as crud_membership,
    member_transaction as crud_member_tx,
    unit_value_history as crud_unit_value,
    fund as crud_fund,
    position as crud_position,
    asset as crud_asset,
)
# Models and Schemas
from backend.models import User, Club, Fund, Asset, Position, ClubMembership, MemberTransaction, UnitValueHistory
from backend.models.enums import AssetType, MemberTransactionType, ClubRole, Currency, OptionType # Added missing enums
# Import schemas that ARE defined in the schemas package
from backend.schemas import MemberTransactionCreate # Import relevant schemas


# Use helpers from CRUD tests for setup
from backend.tests.crud.test_user import create_test_user
# from backend.tests.crud.test_club import create_test_club_via_crud # Use direct CRUD for more control
from backend.tests.crud.test_fund import create_test_fund_via_crud
from backend.tests.crud.test_asset import create_test_stock_asset_via_crud, create_test_option_asset_via_crud
from backend.tests.crud.test_position import create_test_position_via_crud
from backend.tests.crud.test_club_membership import create_test_membership_via_crud
from backend.tests.crud.test_unit_value_history import create_test_unit_value_history_via_crud
from backend.tests.crud.test_member_transaction import create_test_member_transaction_via_crud # Use CRUD helper


# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio

# --- Constants for Mock IDs ---
TEST_USER_ID = uuid.uuid4()
TEST_CLUB_ID = uuid.uuid4()
TEST_FUND_ID = uuid.uuid4()
TEST_MEMBERSHIP_ID = uuid.uuid4()
TEST_ASSET_ID_1 = uuid.uuid4()
TEST_ASSET_ID_2 = uuid.uuid4()
TEST_POSITION_ID_1 = uuid.uuid4()
TEST_POSITION_ID_2 = uuid.uuid4()
TEST_MTX_ID = uuid.uuid4()
TEST_UVH_ID = uuid.uuid4()

# --- Tests for process_member_deposit ---

@patch('sqlalchemy.ext.asyncio.AsyncSession.flush', new_callable=AsyncMock)
@patch('sqlalchemy.ext.asyncio.AsyncSession.add', autospec=True)
@patch('backend.services.accounting_service.crud_member_tx.create_member_transaction', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_unit_value.get_latest_unit_value_for_club', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_club.get_club', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_membership.get_club_membership_by_user_and_club', new_callable=AsyncMock)
async def test_process_member_deposit_first_deposit(
    mock_get_membership: AsyncMock,
    mock_get_club: AsyncMock,
    mock_get_latest_uv: AsyncMock,
    mock_create_mtx: AsyncMock,
    mock_add: MagicMock,
    mock_flush: AsyncMock,
    db_session: AsyncSession
):
    """ Test first member deposit uses initial unit value (mocked). """
    # Arrange
    deposit_amount = Decimal("500.00")
    deposit_in = MemberTransactionCreate(
        user_id=TEST_USER_ID, club_id=TEST_CLUB_ID,
        transaction_type=MemberTransactionType.DEPOSIT, amount=deposit_amount,
        transaction_date=datetime.now(timezone.utc),
        notes="Initial Deposit"
    )
    mock_membership = MagicMock(spec=ClubMembership); mock_membership.id = TEST_MEMBERSHIP_ID
    mock_get_membership.return_value = mock_membership
    mock_club = MagicMock(spec=Club); mock_club.id = TEST_CLUB_ID; mock_club.bank_account_balance = Decimal("0.0")
    mock_get_club.return_value = mock_club
    mock_get_latest_uv.return_value = None
    mock_tx = MagicMock(spec=MemberTransaction); mock_tx.id = TEST_MTX_ID
    mock_create_mtx.return_value = mock_tx

    unit_value_used = accounting_service.INITIAL_UNIT_VALUE
    expected_units = (deposit_amount / unit_value_used).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    expected_final_bank_balance = Decimal("0.0") + deposit_amount
    expected_mtx_data = {
        "membership_id": TEST_MEMBERSHIP_ID, "transaction_type": MemberTransactionType.DEPOSIT,
        "amount": deposit_amount, "transaction_date": deposit_in.transaction_date,
        "unit_value_used": unit_value_used, "units_transacted": expected_units, "notes": deposit_in.notes
    }

    # Act
    result_tx = await accounting_service.process_member_deposit(db=db_session, deposit_in=deposit_in)

    # Assert CRUD calls
    mock_get_membership.assert_called_once_with(db=db_session, user_id=TEST_USER_ID, club_id=TEST_CLUB_ID)
    mock_get_club.assert_called_once_with(db=db_session, club_id=TEST_CLUB_ID)
    mock_get_latest_uv.assert_called_once_with(db=db_session, club_id=TEST_CLUB_ID)
    mock_create_mtx.assert_called_once()
    call_args, call_kwargs = mock_create_mtx.call_args
    assert call_kwargs['member_tx_data']['membership_id'] == expected_mtx_data['membership_id']
    assert call_kwargs['member_tx_data']['unit_value_used'] == expected_mtx_data['unit_value_used']
    assert call_kwargs['member_tx_data']['units_transacted'] == pytest.approx(expected_mtx_data['units_transacted'])
    assert call_kwargs['member_tx_data']['notes'] == expected_mtx_data['notes']
    assert mock_club.bank_account_balance == expected_final_bank_balance
    mock_add.assert_any_call(db_session, mock_club)
    mock_flush.assert_called_once()
    assert result_tx == mock_tx

@patch('sqlalchemy.ext.asyncio.AsyncSession.flush', new_callable=AsyncMock)
@patch('sqlalchemy.ext.asyncio.AsyncSession.add', autospec=True)
@patch('backend.services.accounting_service.crud_member_tx.create_member_transaction', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_unit_value.get_latest_unit_value_for_club', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_club.get_club', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_membership.get_club_membership_by_user_and_club', new_callable=AsyncMock)
async def test_process_member_deposit_subsequent(
    mock_get_membership: AsyncMock,
    mock_get_club: AsyncMock,
    mock_get_latest_uv: AsyncMock,
    mock_create_mtx: AsyncMock,
    mock_add: MagicMock,
    mock_flush: AsyncMock,
    db_session: AsyncSession
):
    """ Test subsequent member deposit uses latest unit value (mocked). """
    # Arrange
    deposit_amount = Decimal("250.00")
    latest_unit_value = Decimal("12.50000000")
    initial_bank_balance = Decimal("1000.00")
    deposit_in = MemberTransactionCreate(
        user_id=TEST_USER_ID, club_id=TEST_CLUB_ID,
        transaction_type=MemberTransactionType.DEPOSIT, amount=deposit_amount,
        transaction_date=datetime.now(timezone.utc),
        notes=None
    )

    mock_membership = MagicMock(spec=ClubMembership); mock_membership.id = TEST_MEMBERSHIP_ID
    mock_get_membership.return_value = mock_membership
    mock_club = MagicMock(spec=Club); mock_club.id = TEST_CLUB_ID; mock_club.bank_account_balance = initial_bank_balance
    mock_get_club.return_value = mock_club
    mock_latest_uv_record = UnitValueHistory(id=uuid.uuid4(), unit_value=latest_unit_value)
    mock_get_latest_uv.return_value = mock_latest_uv_record
    mock_tx = MagicMock(spec=MemberTransaction); mock_tx.id = TEST_MTX_ID
    mock_create_mtx.return_value = mock_tx

    expected_units = (deposit_amount / latest_unit_value).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    expected_final_bank_balance = initial_bank_balance + deposit_amount
    expected_mtx_data = {
        "membership_id": TEST_MEMBERSHIP_ID, "transaction_type": MemberTransactionType.DEPOSIT,
        "amount": deposit_amount, "transaction_date": deposit_in.transaction_date,
        "unit_value_used": latest_unit_value, "units_transacted": expected_units, "notes": deposit_in.notes
    }

    # Act
    result_tx = await accounting_service.process_member_deposit(db=db_session, deposit_in=deposit_in)

    # Assert
    mock_get_membership.assert_called_once_with(db=db_session, user_id=TEST_USER_ID, club_id=TEST_CLUB_ID)
    mock_get_club.assert_called_once_with(db=db_session, club_id=TEST_CLUB_ID)
    mock_get_latest_uv.assert_called_once_with(db=db_session, club_id=TEST_CLUB_ID)
    mock_create_mtx.assert_called_once()
    call_args, call_kwargs = mock_create_mtx.call_args
    assert call_kwargs['member_tx_data']['unit_value_used'] == expected_mtx_data['unit_value_used']
    assert call_kwargs['member_tx_data']['units_transacted'] == pytest.approx(expected_mtx_data['units_transacted'])
    assert call_kwargs['member_tx_data']['notes'] == expected_mtx_data['notes']
    assert mock_club.bank_account_balance == expected_final_bank_balance
    mock_add.assert_any_call(db_session, mock_club)
    mock_flush.assert_called_once()
    assert result_tx == mock_tx

# --- Tests for process_member_withdrawal ---

@patch('sqlalchemy.ext.asyncio.AsyncSession.flush', new_callable=AsyncMock)
@patch('sqlalchemy.ext.asyncio.AsyncSession.add', autospec=True)
@patch('backend.services.accounting_service.crud_member_tx.create_member_transaction', new_callable=AsyncMock)
@patch('backend.crud.member_transaction.get_member_unit_balance', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_unit_value.get_latest_unit_value_for_club', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_club.get_club', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_membership.get_club_membership_by_user_and_club', new_callable=AsyncMock)
async def test_process_member_withdrawal_success(
    mock_get_membership: AsyncMock,
    mock_get_club: AsyncMock,
    mock_get_latest_uv: AsyncMock,
    mock_get_balance: AsyncMock,
    mock_create_mtx: AsyncMock,
    mock_add: MagicMock,
    mock_flush: AsyncMock,
    db_session: AsyncSession
):
    """ Test successful member withdrawal (mocked). """
    # Arrange
    withdrawal_amount = Decimal("1100.00")
    current_member_units = Decimal("150.00000000")
    latest_unit_value = Decimal("11.00000000")
    initial_bank_balance = Decimal("5000.00")

    withdrawal_in = MemberTransactionCreate(
        user_id=TEST_USER_ID, club_id=TEST_CLUB_ID,
        transaction_type=MemberTransactionType.WITHDRAWAL, amount=withdrawal_amount,
        transaction_date=datetime.now(timezone.utc),
        notes="Withdrawal Test"
    )

    mock_membership = MagicMock(spec=ClubMembership); mock_membership.id = TEST_MEMBERSHIP_ID
    mock_get_membership.return_value = mock_membership
    mock_club = MagicMock(spec=Club); mock_club.id = TEST_CLUB_ID; mock_club.bank_account_balance = initial_bank_balance
    mock_get_club.return_value = mock_club
    mock_latest_uv_record = UnitValueHistory(id=uuid.uuid4(), unit_value=latest_unit_value)
    mock_get_latest_uv.return_value = mock_latest_uv_record
    mock_get_balance.return_value = current_member_units
    mock_tx = MagicMock(spec=MemberTransaction); mock_tx.id = TEST_MTX_ID
    mock_create_mtx.return_value = mock_tx

    expected_units_redeemed = (withdrawal_amount / latest_unit_value).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    expected_final_bank_balance = initial_bank_balance - withdrawal_amount
    expected_mtx_data = {
        "membership_id": TEST_MEMBERSHIP_ID, "transaction_type": MemberTransactionType.WITHDRAWAL,
        "amount": withdrawal_amount, "transaction_date": withdrawal_in.transaction_date,
        "unit_value_used": latest_unit_value, "units_transacted": -expected_units_redeemed, "notes": withdrawal_in.notes
    }

    # Act
    result_tx = await accounting_service.process_member_withdrawal(db=db_session, withdrawal_in=withdrawal_in)

    # Assert
    mock_get_membership.assert_called_once_with(db=db_session, user_id=TEST_USER_ID, club_id=TEST_CLUB_ID)
    mock_get_club.assert_called_once_with(db=db_session, club_id=TEST_CLUB_ID)
    mock_get_latest_uv.assert_called_once_with(db=db_session, club_id=TEST_CLUB_ID)
    mock_get_balance.assert_called_once_with(db=db_session, membership_id=TEST_MEMBERSHIP_ID)
    mock_create_mtx.assert_called_once()
    call_args, call_kwargs = mock_create_mtx.call_args
    assert call_kwargs['member_tx_data']['unit_value_used'] == expected_mtx_data['unit_value_used']
    assert call_kwargs['member_tx_data']['units_transacted'] == pytest.approx(expected_mtx_data['units_transacted'])
    assert call_kwargs['member_tx_data']['notes'] == expected_mtx_data['notes']
    assert mock_club.bank_account_balance == expected_final_bank_balance
    mock_add.assert_any_call(db_session, mock_club)
    mock_flush.assert_called_once()
    assert result_tx == mock_tx


# --- Tests for calculate_and_store_nav ---

@patch('backend.services.accounting_service.crud_unit_value.create_unit_value_history', new_callable=AsyncMock)
@patch('backend.crud.member_transaction.get_total_units_for_club', new_callable=AsyncMock)
@patch('backend.services.accounting_service.get_market_prices', new_callable=AsyncMock)
async def test_calculate_and_store_nav_success(
    mock_get_prices: AsyncMock,
    mock_get_units: AsyncMock,
    mock_create_uvh: AsyncMock,
    db_session: AsyncSession
):
    """ Test successful NAV calculation and storage (using real DB objects for setup). """
    # Arrange Phase: Create actual DB objects for the test scope
    valuation_date = date.today()
    creator = await create_test_user(db_session)
    club_data = {"name": "NAV Test Club Real", "creator_id": creator.id, "bank_account_balance": Decimal("1000")}
    test_club = await crud_club.create_club(db=db_session, club_data=club_data)
    test_fund = await create_test_fund_via_crud(db_session, club=test_club)
    test_fund.brokerage_cash_balance = Decimal("5000")
    db_session.add(test_fund)
    test_asset1 = await create_test_stock_asset_via_crud(db_session, symbol="NAV1R")
    test_asset2 = await create_test_stock_asset_via_crud(db_session, symbol="NAV2R")
    pos1 = await create_test_position_via_crud(db_session, fund=test_fund, asset=test_asset1, quantity=Decimal("100"))
    pos2 = await create_test_position_via_crud(db_session, fund=test_fund, asset=test_asset2, quantity=Decimal("50"))
    await db_session.flush()

    # Arrange Mocks
    mock_prices = { test_asset1.id: Decimal("12.00"), test_asset2.id: Decimal("25.00") }
    mock_get_prices.return_value = mock_prices
    total_units = Decimal("850.00000000")
    mock_get_units.return_value = total_units
    mock_history_record = UnitValueHistory(
        id=TEST_UVH_ID, club_id=test_club.id, valuation_date=valuation_date,
        unit_value=Decimal("9.94117647")
    )
    mock_create_uvh.return_value = mock_history_record

    # Expected values
    expected_market_value = (Decimal("100") * Decimal("12.00")) + (Decimal("50") * Decimal("25.00")) # 2450
    await db_session.refresh(test_club)
    await db_session.refresh(test_fund)
    expected_total_cash = test_club.bank_account_balance + test_fund.brokerage_cash_balance # 1000 + 5000 = 6000
    expected_total_club_value = expected_market_value + expected_total_cash # 8450
    expected_unit_value = (expected_total_club_value / total_units).quantize(Decimal("0.00000001")) # 9.94117647
    expected_history_data = {
        "club_id": test_club.id, "valuation_date": valuation_date,
        "total_club_value": expected_total_club_value.quantize(Decimal("0.01")),
        "total_units_outstanding": total_units,
        "unit_value": expected_unit_value
    }
    expected_asset_ids = {test_asset1.id, test_asset2.id}

    # Act
    result_history = await accounting_service.calculate_and_store_nav(
        db=db_session, club_id=test_club.id, valuation_date=valuation_date
    )

    # Assert Mocks
    mock_get_prices.assert_called_once()
    call_args, call_kwargs = mock_get_prices.call_args
    assert call_args[0] == db_session # db session is arg 0
    assert set(call_args[1]) == expected_asset_ids # asset_ids is arg 1
    # --- FIX: Assert correct argument index for valuation_date ---
    assert call_args[2] == valuation_date # valuation_date is arg 2
    # --- END FIX ---

    mock_get_units.assert_called_once_with(db=db_session, club_id=test_club.id)

    # Check create_unit_value_history call
    mock_create_uvh.assert_called_once()
    call_args_create, call_kwargs_create = mock_create_uvh.call_args
    created_data = call_kwargs_create['uvh_data']
    assert created_data['club_id'] == expected_history_data['club_id']
    assert created_data['valuation_date'] == expected_history_data['valuation_date']
    assert created_data['total_club_value'] == pytest.approx(expected_history_data['total_club_value'])
    assert created_data['total_units_outstanding'] == pytest.approx(expected_history_data['total_units_outstanding'])
    assert created_data['unit_value'] == pytest.approx(expected_history_data['unit_value'])

    # Check return value
    assert result_history == mock_history_record


@patch('backend.services.accounting_service.crud_unit_value.create_unit_value_history', new_callable=AsyncMock)
@patch('backend.crud.member_transaction.get_total_units_for_club', new_callable=AsyncMock)
@patch('backend.services.accounting_service.get_market_prices', new_callable=AsyncMock)
async def test_calculate_and_store_nav_duplicate_date(
    mock_get_prices: AsyncMock,
    mock_get_units: AsyncMock,
    mock_create_uvh: AsyncMock,
    db_session: AsyncSession
):
    """Test NAV calculation raises 409 if create_unit_value_history raises IntegrityError."""
    # Arrange: Setup club using real objects via db_session
    valuation_date = date.today()
    creator = await create_test_user(db_session)
    club_data = {"name": "NAV Dup Test Real", "creator_id": creator.id}
    test_club = await crud_club.create_club(db=db_session, club_data=club_data)
    await create_test_fund_via_crud(db_session, club=test_club)
    await db_session.flush()

    # Arrange Mocks
    mock_get_prices.return_value = {}
    mock_get_units.return_value = Decimal("1000")
    mock_create_uvh.side_effect = IntegrityError("Mock Duplicate Date Error", params={}, orig=Exception())

    # Act & Assert: Expect 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        await accounting_service.calculate_and_store_nav(
            db=db_session, club_id=test_club.id, valuation_date=valuation_date
        )

    assert exc_info.value.status_code == 409
    assert f"Unit value history for club {test_club.id} on {valuation_date} already exists" in exc_info.value.detail
    mock_get_prices.assert_called_once()
    mock_get_units.assert_called_once_with(db=db_session, club_id=test_club.id)
    mock_create_uvh.assert_called_once()


async def test_calculate_and_store_nav_club_not_found(db_session: AsyncSession):
    """Test NAV calculation raises 404 if club not found (no mocking needed)."""
    non_existent_club_id = uuid.uuid4()
    valuation_date = date.today()
    with pytest.raises(HTTPException) as exc_info:
        await accounting_service.calculate_and_store_nav(
            db=db_session, club_id=non_existent_club_id, valuation_date=valuation_date
        )
    assert exc_info.value.status_code == 404
    assert f"Club {non_existent_club_id} not found" in exc_info.value.detail


# --- Tests for get_member_equity ---

@patch('backend.crud.member_transaction.get_member_unit_balance', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_unit_value.get_latest_unit_value_for_club', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_membership.get_club_membership_by_user_and_club', new_callable=AsyncMock)
async def test_get_member_equity_success(
    mock_get_membership: AsyncMock,
    mock_get_latest_uv: AsyncMock,
    mock_get_balance: AsyncMock,
    db_session: AsyncSession
):
    """ Test successful calculation of member equity. """
    member_units = Decimal("123.45678900"); mock_get_balance.return_value = member_units
    latest_unit_value = Decimal("10.54321000")
    mock_membership = MagicMock(spec=ClubMembership); mock_membership.id = TEST_MEMBERSHIP_ID
    mock_get_membership.return_value = mock_membership
    mock_latest_uv_record = UnitValueHistory(id=uuid.uuid4(), unit_value=latest_unit_value)
    mock_get_latest_uv.return_value = mock_latest_uv_record
    expected_equity = (member_units * latest_unit_value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    result_equity = await accounting_service.get_member_equity(db=db_session, club_id=TEST_CLUB_ID, user_id=TEST_USER_ID)
    mock_get_membership.assert_called_once_with(db=db_session, user_id=TEST_USER_ID, club_id=TEST_CLUB_ID)
    mock_get_balance.assert_called_once_with(db=db_session, membership_id=TEST_MEMBERSHIP_ID)
    mock_get_latest_uv.assert_called_once_with(db=db_session, club_id=TEST_CLUB_ID)
    assert result_equity == pytest.approx(expected_equity)

@patch('backend.crud.member_transaction.get_member_unit_balance', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_unit_value.get_latest_unit_value_for_club', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_membership.get_club_membership_by_user_and_club', new_callable=AsyncMock)
async def test_get_member_equity_zero_units(
    mock_get_membership: AsyncMock,
    mock_get_latest_uv: AsyncMock,
    mock_get_balance: AsyncMock,
    db_session: AsyncSession
):
    """ Test equity calculation when member has zero units. """
    mock_get_balance.return_value = Decimal("0.0")
    mock_membership = MagicMock(spec=ClubMembership); mock_membership.id = TEST_MEMBERSHIP_ID
    mock_get_membership.return_value = mock_membership
    mock_get_latest_uv.return_value = UnitValueHistory(id=uuid.uuid4(), unit_value=Decimal("10.0"))
    result_equity = await accounting_service.get_member_equity(db=db_session, club_id=TEST_CLUB_ID, user_id=TEST_USER_ID)
    mock_get_membership.assert_called_once_with(db=db_session, user_id=TEST_USER_ID, club_id=TEST_CLUB_ID)
    mock_get_balance.assert_called_once_with(db=db_session, membership_id=TEST_MEMBERSHIP_ID)
    mock_get_latest_uv.assert_not_called()
    assert result_equity == Decimal("0.00")


@patch('backend.crud.member_transaction.get_member_unit_balance', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_unit_value.get_latest_unit_value_for_club', new_callable=AsyncMock)
@patch('backend.services.accounting_service.crud_membership.get_club_membership_by_user_and_club', new_callable=AsyncMock)
async def test_get_member_equity_no_nav_history(
    mock_get_membership: AsyncMock,
    mock_get_latest_uv: AsyncMock,
    mock_get_balance: AsyncMock,
    db_session: AsyncSession
):
    """ Test equity calculation returns 0 if no NAV history exists. """
    mock_get_balance.return_value = Decimal("50.0")
    mock_membership = MagicMock(spec=ClubMembership); mock_membership.id = TEST_MEMBERSHIP_ID
    mock_get_membership.return_value = mock_membership
    mock_get_latest_uv.return_value = None
    result_equity = await accounting_service.get_member_equity(db=db_session, club_id=TEST_CLUB_ID, user_id=TEST_USER_ID)
    mock_get_membership.assert_called_once_with(db=db_session, user_id=TEST_USER_ID, club_id=TEST_CLUB_ID)
    mock_get_balance.assert_called_once_with(db=db_session, membership_id=TEST_MEMBERSHIP_ID)
    mock_get_latest_uv.assert_called_once_with(db=db_session, club_id=TEST_CLUB_ID)
    assert result_equity == Decimal("0.00")

@patch('backend.services.accounting_service.crud_membership.get_club_membership_by_user_and_club', new_callable=AsyncMock)
async def test_get_member_equity_membership_not_found(mock_get_membership: AsyncMock, db_session: AsyncSession):
    """ Test equity calculation fails if membership not found. """
    mock_get_membership.return_value = None
    with pytest.raises(HTTPException) as exc_info:
        await accounting_service.get_member_equity(db=db_session, club_id=TEST_CLUB_ID, user_id=TEST_USER_ID)
    assert exc_info.value.status_code == 404
    assert "Membership for user" in exc_info.value.detail
    mock_get_membership.assert_called_once_with(db=db_session, user_id=TEST_USER_ID, club_id=TEST_CLUB_ID)

