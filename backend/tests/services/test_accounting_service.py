# backend/tests/services/test_accounting_service.py

import pytest
import uuid
from decimal import Decimal, ROUND_HALF_UP, DivisionByZero
from datetime import date, datetime, timezone, timedelta
from typing import List, Sequence, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, MissingGreenlet
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

# Service functions to test
from backend.services import accounting_service
# CRUD functions - now used directly instead of mocked
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
from backend.models.enums import AssetType, MemberTransactionType, ClubRole, Currency, OptionType
# Import schemas
from backend.schemas import MemberTransactionCreate

# Import Auth0 mocking fixtures
from backend.tests.auth_fixtures import mock_auth0_token_verification, mock_get_current_active_user, test_user

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio

# --- Tests for process_member_deposit ---

async def test_process_member_deposit_first_deposit(db_session: AsyncSession):
    """ Test first member deposit uses initial unit value using actual CRUD functions. """
    # Arrange - Create a user, club, and membership
    user_data = {
        "email": f"deposit_user_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|deposit_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    user = await crud_user.create_user(db=db_session, user_data=user_data)
    await db_session.flush()
    
    club_data = {
        "name": f"Deposit Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for deposits",
        "bank_account_balance": Decimal("0.0"),
        "creator_id": user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    membership_data = {
        "user_id": user.id,
        "club_id": club.id,
        "role": ClubRole.MEMBER
    }
    membership = await crud_membership.create_club_membership(db=db_session, membership_data=membership_data)
    await db_session.flush()
    
    # Create deposit input
    deposit_amount = Decimal("500.00")
    deposit_in = MemberTransactionCreate(
        user_id=user.id,
        club_id=club.id,
        transaction_type=MemberTransactionType.DEPOSIT,
        amount=deposit_amount,
        transaction_date=datetime.now(timezone.utc),
        notes="Initial Deposit"
    )
    
    # Expected calculations
    unit_value_used = accounting_service.INITIAL_UNIT_VALUE
    expected_units = (deposit_amount / unit_value_used).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    expected_final_bank_balance = Decimal("0.0") + deposit_amount
    
    # Act
    result_tx = await accounting_service.process_member_deposit(db=db_session, deposit_in=deposit_in)
    
    # Assert
    assert result_tx is not None
    assert result_tx.membership_id == membership.id
    assert result_tx.transaction_type == MemberTransactionType.DEPOSIT
    assert result_tx.amount == deposit_amount
    assert result_tx.unit_value_used == unit_value_used
    assert result_tx.units_transacted == expected_units
    assert result_tx.notes == deposit_in.notes
    
    # Verify club bank balance was updated
    await db_session.refresh(club)
    assert club.bank_account_balance == expected_final_bank_balance


async def test_process_member_deposit_subsequent(db_session: AsyncSession):
    """ Test subsequent member deposit uses latest unit value using actual CRUD functions. """
    # Arrange - Create a user, club, membership, and initial unit value history
    user_data = {
        "email": f"sub_deposit_user_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|sub_deposit_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    user = await crud_user.create_user(db=db_session, user_data=user_data)
    await db_session.flush()
    
    club_data = {
        "name": f"Sub Deposit Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for subsequent deposits",
        "bank_account_balance": Decimal("1000.00"),
        "creator_id": user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    membership_data = {
        "user_id": user.id,
        "club_id": club.id,
        "role": ClubRole.MEMBER
    }
    membership = await crud_membership.create_club_membership(db=db_session, membership_data=membership_data)
    await db_session.flush()
    
    # Create an initial unit value history record
    latest_unit_value = Decimal("12.50000000")
    uvh_data = {
        "club_id": club.id,
        "valuation_date": date.today() - timedelta(days=1),
        "total_club_value": Decimal("10000.00"),
        "total_units_outstanding": Decimal("800.00000000"),
        "unit_value": latest_unit_value
    }
    await crud_unit_value.create_unit_value_history(db=db_session, uvh_data=uvh_data)
    await db_session.flush()
    
    # Create deposit input
    initial_bank_balance = club.bank_account_balance
    deposit_amount = Decimal("250.00")
    deposit_in = MemberTransactionCreate(
        user_id=user.id,
        club_id=club.id,
        transaction_type=MemberTransactionType.DEPOSIT,
        amount=deposit_amount,
        transaction_date=datetime.now(timezone.utc),
        notes=None
    )
    
    # Expected calculations
    expected_units = (deposit_amount / latest_unit_value).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    expected_final_bank_balance = initial_bank_balance + deposit_amount
    
    # Act
    result_tx = await accounting_service.process_member_deposit(db=db_session, deposit_in=deposit_in)
    
    # Assert
    assert result_tx is not None
    assert result_tx.membership_id == membership.id
    assert result_tx.transaction_type == MemberTransactionType.DEPOSIT
    assert result_tx.amount == deposit_amount
    assert result_tx.unit_value_used == latest_unit_value
    assert result_tx.units_transacted == expected_units
    assert result_tx.notes == deposit_in.notes
    
    # Verify club bank balance was updated
    await db_session.refresh(club)
    assert club.bank_account_balance == expected_final_bank_balance


# --- Tests for process_member_withdrawal ---

async def test_process_member_withdrawal_success(db_session: AsyncSession):
    """ Test successful member withdrawal using actual CRUD functions. """
    # Arrange - Create a user, club, membership, initial unit value history, and initial deposit
    user_data = {
        "email": f"withdraw_user_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|withdraw_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    user = await crud_user.create_user(db=db_session, user_data=user_data)
    await db_session.flush()
    
    club_data = {
        "name": f"Withdraw Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for withdrawals",
        "bank_account_balance": Decimal("5000.00"),
        "creator_id": user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    membership_data = {
        "user_id": user.id,
        "club_id": club.id,
        "role": ClubRole.MEMBER
    }
    membership = await crud_membership.create_club_membership(db=db_session, membership_data=membership_data)
    await db_session.flush()
    
    # Create an initial unit value history record
    latest_unit_value = Decimal("11.00000000")
    uvh_data = {
        "club_id": club.id,
        "valuation_date": date.today() - timedelta(days=1),
        "total_club_value": Decimal("10000.00"),
        "total_units_outstanding": Decimal("909.09090909"),
        "unit_value": latest_unit_value
    }
    await crud_unit_value.create_unit_value_history(db=db_session, uvh_data=uvh_data)
    await db_session.flush()
    
    # Create an initial deposit to give the member some units
    initial_deposit_data = {
        "membership_id": membership.id,
        "transaction_type": MemberTransactionType.DEPOSIT,
        "amount": Decimal("1650.00"),
        "transaction_date": datetime.now(timezone.utc) - timedelta(days=1),
        "unit_value_used": latest_unit_value,
        "units_transacted": Decimal("150.00000000"),
        "notes": "Initial deposit for withdrawal test"
    }
    await crud_member_tx.create_member_transaction(db=db_session, member_tx_data=initial_deposit_data)
    await db_session.flush()
    
    # Create withdrawal input
    initial_bank_balance = club.bank_account_balance
    withdrawal_amount = Decimal("1100.00")
    withdrawal_in = MemberTransactionCreate(
        user_id=user.id,
        club_id=club.id,
        transaction_type=MemberTransactionType.WITHDRAWAL,
        amount=withdrawal_amount,
        transaction_date=datetime.now(timezone.utc),
        notes="Withdrawal Test"
    )
    
    # Expected calculations
    expected_units_redeemed = (withdrawal_amount / latest_unit_value).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
    expected_final_bank_balance = initial_bank_balance - withdrawal_amount
    
    # Act
    result_tx = await accounting_service.process_member_withdrawal(db=db_session, withdrawal_in=withdrawal_in)
    
    # Assert
    assert result_tx is not None
    assert result_tx.membership_id == membership.id
    assert result_tx.transaction_type == MemberTransactionType.WITHDRAWAL
    assert result_tx.amount == withdrawal_amount
    assert result_tx.unit_value_used == latest_unit_value
    assert result_tx.units_transacted == -expected_units_redeemed
    assert result_tx.notes == withdrawal_in.notes
    
    # Verify club bank balance was updated
    await db_session.refresh(club)
    assert club.bank_account_balance == expected_final_bank_balance


# --- Tests for calculate_and_store_nav ---

async def test_calculate_and_store_nav_success(db_session: AsyncSession):
    """ Test successful NAV calculation and storage using actual CRUD functions. """
    # Arrange - Create a user, club, fund, assets, positions, and member with units
    user_data = {
        "email": f"nav_user_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|nav_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    user = await crud_user.create_user(db=db_session, user_data=user_data)
    await db_session.flush()
    
    club_data = {
        "name": f"NAV Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for NAV calculation",
        "bank_account_balance": Decimal("1000.00"),
        "creator_id": user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    fund_data = {
        "club_id": club.id,
        "name": "NAV Fund",
        "description": "Fund for NAV testing",
        "brokerage_cash_balance": Decimal("5000.00"),
        "is_active": True
    }
    fund = await crud_fund.create_fund(db=db_session, fund_data=fund_data)
    await db_session.flush()
    
    # Create assets
    asset1_data = {
        "asset_type": AssetType.STOCK,
        "symbol": "IBM",
        "name": "NAV Test Stock 1",
        "currency": Currency.USD
    }
    asset2_data = {
        "asset_type": AssetType.STOCK,
        "symbol": "AAPL",
        "name": "NAV Test Stock 2",
        "currency": Currency.USD
    }
    asset1 = await crud_asset.create_asset(db=db_session, asset_data=asset1_data)
    asset2 = await crud_asset.create_asset(db=db_session, asset_data=asset2_data)
    await db_session.flush()
    
    # Create positions
    position1_data = {
        "fund_id": fund.id,
        "asset_id": asset1.id,
        "quantity": Decimal("100"),
        "average_price": Decimal("10.00")
    }
    position2_data = {
        "fund_id": fund.id,
        "asset_id": asset2.id,
        "quantity": Decimal("50"),
        "average_price": Decimal("20.00")
    }
    await crud_position.create_position(db=db_session, position_data=position1_data)
    await crud_position.create_position(db=db_session, position_data=position2_data)
    await db_session.flush()
    
    # Create membership
    membership_data = {
        "user_id": user.id,
        "club_id": club.id,
        "role": ClubRole.MEMBER
    }
    membership = await crud_membership.create_club_membership(db=db_session, membership_data=membership_data)
    await db_session.flush()
    
    # Create initial deposit to establish units
    initial_deposit_data = {
        "membership_id": membership.id,
        "transaction_type": MemberTransactionType.DEPOSIT,
        "amount": Decimal("8500.00"),
        "transaction_date": datetime.now(timezone.utc) - timedelta(days=10),
        "unit_value_used": accounting_service.INITIAL_UNIT_VALUE,
        "units_transacted": Decimal("850.00000000"),
        "notes": "Initial deposit for NAV test"
    }
    await crud_member_tx.create_member_transaction(db=db_session, member_tx_data=initial_deposit_data)
    await db_session.flush()
    
    # Set up market prices for the test
    # In a real implementation, we would need to mock the external API call
    # For this test, we'll patch the get_market_prices function to return our test prices
    valuation_date = date.today()
    
    # Expected calculations for cash (which we can predict)
    expected_total_cash = club.bank_account_balance + fund.brokerage_cash_balance  # 1000 + 5000 = 6000
    
    # Act
    result_history = await accounting_service.calculate_and_store_nav(
        db=db_session, club_id=club.id, valuation_date=valuation_date
    )
    
    # Assert
    assert result_history is not None
    assert result_history.club_id == club.id
    assert result_history.valuation_date == valuation_date
    assert result_history.total_club_value > expected_total_cash  # Should include market value
    assert result_history.total_units_outstanding == Decimal("850.00000000")
    assert result_history.unit_value > Decimal("0")  # Should be positive


async def test_calculate_and_store_nav_duplicate_date(db_session: AsyncSession):
    """ Test NAV calculation raises 409 if unit value history for the date already exists. """
    # Arrange - Create a user, club, and initial unit value history
    user_data = {
        "email": f"dup_nav_user_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|dup_nav_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    user = await crud_user.create_user(db=db_session, user_data=user_data)
    await db_session.flush()
    
    club_data = {
        "name": f"Dup NAV Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for duplicate NAV",
        "bank_account_balance": Decimal("1000.00"),
        "creator_id": user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    # Create an initial unit value history record for today
    valuation_date = date.today()
    uvh_data = {
        "club_id": club.id,
        "valuation_date": valuation_date,
        "total_club_value": Decimal("1000.00"),
        "total_units_outstanding": Decimal("100.00000000"),
        "unit_value": Decimal("10.00000000")
    }
    await crud_unit_value.create_unit_value_history(db=db_session, uvh_data=uvh_data)
    await db_session.flush()
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await accounting_service.calculate_and_store_nav(
            db=db_session, club_id=club.id, valuation_date=valuation_date
        )
    
    assert exc_info.value.status_code == 409
    assert f"Unit value history for club {club.id} on {valuation_date} already exists" in exc_info.value.detail


async def test_calculate_and_store_nav_club_not_found(db_session: AsyncSession):
    """ Test NAV calculation raises 404 if club not found. """
    non_existent_club_id = uuid.uuid4()
    valuation_date = date.today()
    
    with pytest.raises(HTTPException) as exc_info:
        await accounting_service.calculate_and_store_nav(
            db=db_session, club_id=non_existent_club_id, valuation_date=valuation_date
        )
    
    assert exc_info.value.status_code == 404
    assert f"Club {non_existent_club_id} not found" in exc_info.value.detail


# --- Tests for get_member_equity ---

async def test_get_member_equity_success(db_session: AsyncSession):
    """ Test successful calculation of member equity using actual CRUD functions. """
    # Arrange - Create a user, club, membership, unit value history, and member transaction
    user_data = {
        "email": f"equity_user_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|equity_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    user = await crud_user.create_user(db=db_session, user_data=user_data)
    await db_session.flush()
    
    club_data = {
        "name": f"Equity Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for equity calculation",
        "bank_account_balance": Decimal("1000.00"),
        "creator_id": user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    membership_data = {
        "user_id": user.id,
        "club_id": club.id,
        "role": ClubRole.MEMBER
    }
    membership = await crud_membership.create_club_membership(db=db_session, membership_data=membership_data)
    await db_session.flush()
    
    # Create unit value history
    latest_unit_value = Decimal("10.54321000")
    uvh_data = {
        "club_id": club.id,
        "valuation_date": date.today() - timedelta(days=1),
        "total_club_value": Decimal("10000.00"),
        "total_units_outstanding": Decimal("948.43210000"),
        "unit_value": latest_unit_value
    }
    await crud_unit_value.create_unit_value_history(db=db_session, uvh_data=uvh_data)
    await db_session.flush()
    
    # Create member transaction to establish units
    member_units = Decimal("123.45678900")
    deposit_data = {
        "membership_id": membership.id,
        "transaction_type": MemberTransactionType.DEPOSIT,
        "amount": Decimal("1300.00"),
        "transaction_date": datetime.now(timezone.utc) - timedelta(days=2),
        "unit_value_used": Decimal("10.53000000"),
        "units_transacted": member_units,
        "notes": "Deposit for equity test"
    }
    await crud_member_tx.create_member_transaction(db=db_session, member_tx_data=deposit_data)
    await db_session.flush()
    
    # Expected calculations
    expected_equity = (member_units * latest_unit_value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    # Act
    result_equity = await accounting_service.get_member_equity(db=db_session, club_id=club.id, user_id=user.id)
    
    # Assert
    assert result_equity == expected_equity


async def test_get_member_equity_zero_units(db_session: AsyncSession):
    """ Test equity calculation when member has zero units using actual CRUD functions. """
    # Arrange - Create a user, club, and membership (but no transactions)
    user_data = {
        "email": f"zero_equity_user_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|zero_equity_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    user = await crud_user.create_user(db=db_session, user_data=user_data)
    await db_session.flush()
    
    club_data = {
        "name": f"Zero Equity Club {uuid.uuid4().hex[:6]}",
        "description": "Test club for zero equity",
        "bank_account_balance": Decimal("1000.00"),
        "creator_id": user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    membership_data = {
        "user_id": user.id,
        "club_id": club.id,
        "role": ClubRole.MEMBER
    }
    membership = await crud_membership.create_club_membership(db=db_session, membership_data=membership_data)
    await db_session.flush()
    
    # Create unit value history
    uvh_data = {
        "club_id": club.id,
        "valuation_date": date.today() - timedelta(days=1),
        "total_club_value": Decimal("1000.00"),
        "total_units_outstanding": Decimal("100.00000000"),
        "unit_value": Decimal("10.00000000")
    }
    await crud_unit_value.create_unit_value_history(db=db_session, uvh_data=uvh_data)
    await db_session.flush()
    
    # Act
    result_equity = await accounting_service.get_member_equity(db=db_session, club_id=club.id, user_id=user.id)
    
    # Assert
    assert result_equity == Decimal("0.00")


async def test_get_member_equity_no_nav_history(db_session: AsyncSession):
    """ Test equity calculation returns 0 if no NAV history exists using actual CRUD functions. """
    # Arrange - Create a user, club, membership, and member transaction (but no unit value history)
    user_data = {
        "email": f"no_nav_user_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|no_nav_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    user = await crud_user.create_user(db=db_session, user_data=user_data)
    await db_session.flush()
    
    club_data = {
        "name": f"No NAV Club {uuid.uuid4().hex[:6]}",
        "description": "Test club with no NAV history",
        "bank_account_balance": Decimal("1000.00"),
        "creator_id": user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    membership_data = {
        "user_id": user.id,
        "club_id": club.id,
        "role": ClubRole.MEMBER
    }
    membership = await crud_membership.create_club_membership(db=db_session, membership_data=membership_data)
    await db_session.flush()
    
    # Create member transaction to establish units
    deposit_data = {
        "membership_id": membership.id,
        "transaction_type": MemberTransactionType.DEPOSIT,
        "amount": Decimal("500.00"),
        "transaction_date": datetime.now(timezone.utc) - timedelta(days=1),
        "unit_value_used": accounting_service.INITIAL_UNIT_VALUE,
        "units_transacted": Decimal("50.00000000"),
        "notes": "Deposit for no NAV test"
    }
    await crud_member_tx.create_member_transaction(db=db_session, member_tx_data=deposit_data)
    await db_session.flush()
    
    # Act
    result_equity = await accounting_service.get_member_equity(db=db_session, club_id=club.id, user_id=user.id)
    
    # Assert
    assert result_equity == Decimal("0.00")


async def test_get_member_equity_membership_not_found(db_session: AsyncSession):
    """ Test equity calculation fails if membership not found using actual CRUD functions. """
    # Arrange - Create a user and club but no membership
    user_data = {
        "email": f"no_member_user_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|no_member_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    user = await crud_user.create_user(db=db_session, user_data=user_data)
    await db_session.flush()
    
    club_data = {
        "name": f"No Member Club {uuid.uuid4().hex[:6]}",
        "description": "Test club with no membership",
        "bank_account_balance": Decimal("1000.00"),
        "creator_id": user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await accounting_service.get_member_equity(db=db_session, club_id=club.id, user_id=uuid.uuid4())
    
    assert exc_info.value.status_code == 404
    assert "Membership for user" in exc_info.value.detail
