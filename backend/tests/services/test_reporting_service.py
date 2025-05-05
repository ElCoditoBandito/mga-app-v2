# backend/tests/services/test_reporting_service.py

import pytest
import uuid
from decimal import Decimal, ROUND_HALF_UP, DivisionByZero
from datetime import date, datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock, call, MagicMock # Import call
from typing import List, Sequence, Optional # Added List, Sequence, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, MissingGreenlet # Added for potential use
from sqlalchemy.orm import selectinload # Import selectinload
from fastapi import HTTPException

# Service functions to test
from backend.services import reporting_service
# Import the response models defined within the service file
from backend.services.reporting_service import MemberStatementData, ClubPerformanceData
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
from backend.schemas import ClubPortfolio, MemberTransactionCreate, PositionRead, UnitValueHistoryRead, MemberTransactionRead, ClubPortfolio # Import response schemas


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

# --- Helper Function to Setup Context ---

# FIX: Added initial_unit_value and valuation_date_for_initial parameters
async def setup_reporting_test_context(
    db_session: AsyncSession,
    num_members: int = 1,
    num_funds: int = 1,
    num_positions_per_fund: int = 1,
    num_history_points: int = 1,
    initial_unit_value: Optional[Decimal] = None, # Added parameter
    valuation_date_for_initial: Optional[date] = None # Added parameter
) -> tuple[User, Club, List[ClubMembership], List[Fund], List[Position], List[UnitValueHistory]]:
    """Creates a more complex setup for reporting tests."""
    creator = await create_test_user(db_session, email=f"rep_cr_{uuid.uuid4().hex[:4]}@test.com")
    club_data = {"name": f"ReportTestClub_{uuid.uuid4().hex[:6]}", "creator_id": creator.id, "bank_account_balance": Decimal("1000.00")}
    club = await crud_club.create_club(db=db_session, club_data=club_data) # Use direct CRUD
    admin_membership = await crud_membership.create_club_membership(db=db_session, membership_data={"user_id": creator.id, "club_id": club.id, "role": ClubRole.ADMIN})

    memberships = [admin_membership]
    for i in range(num_members - 1):
        member_user = await create_test_user(db_session, email=f"rep_mem{i}_{uuid.uuid4().hex[:4]}@test.com")
        # Use helper for subsequent memberships
        member_membership = await create_test_membership_via_crud(db_session, user=member_user, club=club)
        memberships.append(member_membership)

    funds = []
    positions = []
    assets = []
    for i in range(num_funds):
        fund = await create_test_fund_via_crud(db_session, club=club, name=f"Report Fund {i+1}")
        fund.brokerage_cash_balance = Decimal("500.00") * (i + 1)
        db_session.add(fund)
        funds.append(fund)
        for j in range(num_positions_per_fund):
            asset = await create_test_stock_asset_via_crud(db_session, symbol=f"REP{i}{j}")
            assets.append(asset)
            pos = await create_test_position_via_crud(db_session, fund=fund, asset=asset, quantity=Decimal(10*(i+1)*(j+1)), avg_cost=Decimal(5*(i+1)*(j+1)))
            positions.append(pos)

    history = []
    base_unit_value = Decimal("10.0")
    base_total_value = Decimal("10000")
    base_total_units = Decimal("1000")

    # Create the initial unit value if provided
    temp_num_history_points = num_history_points # Use temp variable
    if initial_unit_value is not None:
        val_date = valuation_date_for_initial or date.today() - timedelta(days=temp_num_history_points) # Use provided date or default offset
        # Ensure it doesn't clash with loop below if num_history_points is 1
        if temp_num_history_points == 1 and val_date >= date.today(): # Check if val_date is today or future
             val_date = date.today() - timedelta(days=1)

        # Use the CRUD helper to create the history point
        hist = await create_test_unit_value_history_via_crud(
            db_session, club=club, valuation_date=val_date,
            total_club_value=initial_unit_value * base_total_units, # Calculate plausible total value
            total_units_outstanding=base_total_units,
            unit_value=initial_unit_value
        )
        history.append(hist)
        # Adjust num_history_points if we manually created one to avoid date clashes or duplicates
        # Calculate remaining points needed based on the date of the initial point created
        days_diff = (date.today() - val_date).days
        # Calculate how many loop iterations to skip
        skip_iterations = days_diff - (num_history_points - 1)
        temp_num_history_points = max(0, num_history_points - skip_iterations -1)


    # Create remaining history points
    for i in range(temp_num_history_points):
        # Calculate date relative to today, ensuring no duplicates with initial point
        hist_date = date.today() - timedelta(days=temp_num_history_points - 1 - i)
        # Avoid creating duplicate for the same date if initial_unit_value was set for that date
        if any(h.valuation_date == hist_date for h in history):
            continue
        unit_val = base_unit_value + Decimal(i) * Decimal("0.1")
        # Use the CRUD helper to create history points
        hist = await create_test_unit_value_history_via_crud(
            db_session, club=club, valuation_date=hist_date,
            total_club_value=base_total_value + Decimal(i*100),
            total_units_outstanding=base_total_units + Decimal(i*10),
            unit_value=unit_val
        )
        history.append(hist)

    await db_session.flush()
    # Return creator user along with other objects
    return creator, club, memberships, funds, positions, history


# --- Tests for get_club_portfolio_report ---

@patch('backend.services.accounting_service.get_market_prices', new_callable=AsyncMock)
async def test_get_club_portfolio_report_success(mock_get_prices: AsyncMock, db_session: AsyncSession):
    """Test generating a successful club portfolio report."""
    # Arrange
    num_funds = 2
    num_pos_per_fund = 2
    # Use the setup helper
    _creator, club, _memberships, funds, positions, history = await setup_reporting_test_context(
        db_session, num_funds=num_funds, num_positions_per_fund=num_pos_per_fund, num_history_points=1
    )
    valuation_date = date.today()
    # Fetch the latest history record again to ensure relationships are loaded if needed by schema validation
    # The service function itself should handle loading relationships needed for its internal logic
    latest_hist_model = await crud_unit_value.get_latest_unit_value_for_club(db=db_session, club_id=club.id)
    assert latest_hist_model is not None # Ensure it exists

    # Mock market prices
    mock_prices = {}
    expected_market_value = Decimal("0.0")
    pos_count = 0
    expected_asset_ids = set() # Use set for expected IDs
    # Ensure relationships are loaded on position objects fetched by the setup helper
    # before passing them implicitly to the service function via the club object
    for pos in positions:
        # Refresh relationships needed by the service or schema validation
        await db_session.refresh(pos, attribute_names=['asset', 'fund']) # Load asset and fund
        assert pos.asset is not None, f"Asset relationship not loaded for position {pos.id}"
        assert pos.fund is not None, f"Fund relationship not loaded for position {pos.id}"

        price = Decimal("10.00") + Decimal(pos_count) # Simple mock price
        # Use the asset_id from the refreshed object
        if pos.asset_id:
            mock_prices[pos.asset_id] = price
            expected_market_value += pos.quantity * price
            expected_asset_ids.add(pos.asset_id) # Add ID to set
        pos_count += 1
    mock_get_prices.return_value = mock_prices

    # Fetch club again to refresh balances potentially changed during setup flush
    await db_session.refresh(club)
    for f in funds:
        await db_session.refresh(f)
    expected_total_cash = club.bank_account_balance + sum(f.brokerage_cash_balance for f in funds)

    # Act
    # Call the actual service function
    print("Attempting manual rebuild for ClubPortfolio in test...")
    try:
        # Import the specific schemas needed for rebuild within the test scope
        from backend.schemas.club import ClubPortfolio
        from backend.schemas.position import PositionRead
        from backend.schemas.unit_value import UnitValueHistoryRead
        ClubPortfolio.model_rebuild(force=True)
        print("ClubPortfolio rebuild successful in test.")
    except Exception as e:
        print(f"ClubPortfolio rebuild failed in test: {e}")
    report = await reporting_service.get_club_portfolio_report(
        db=db_session, club_id=club.id, valuation_date=valuation_date
    )

    # Assert
    assert isinstance(report, ClubPortfolio)
    assert report.club_id == club.id
    assert report.valuation_date == valuation_date
    assert report.total_market_value == pytest.approx(expected_market_value.quantize(Decimal("0.01")))
    assert report.total_cash_value == pytest.approx(expected_total_cash.quantize(Decimal("0.01")))
    assert len(report.aggregated_positions) == num_funds * num_pos_per_fund
    assert report.recent_unit_value is not None
    # Access the unit_value attribute from the validated Pydantic model within the report
    assert report.recent_unit_value.unit_value == latest_hist_model.unit_value

    # Check mock call (order-independent)
    mock_get_prices.assert_called_once()
    actual_call_args, actual_call_kwargs = mock_get_prices.call_args
    # Assert the db session, asset IDs, and date arguments
    assert actual_call_args[0] == db_session # db session is arg 0
    assert isinstance(actual_call_args[1], list) # asset_ids is arg 1
    assert set(actual_call_args[1]) == expected_asset_ids # Compare sets
    assert actual_call_args[2] == valuation_date # date is arg 2


async def test_get_club_portfolio_report_club_not_found(db_session: AsyncSession):
    """Test report generation fails if club doesn't exist."""
    non_existent_club_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        await reporting_service.get_club_portfolio_report(db=db_session, club_id=non_existent_club_id)
    assert exc_info.value.status_code == 404


# --- Tests for get_member_statement ---

# FIX: Pass the correct parameter name 'valuation_date_for_initial' to helper
@patch('backend.crud.member_transaction.get_member_unit_balance', new_callable=AsyncMock)
async def test_get_member_statement_success(mock_get_balance: AsyncMock, db_session: AsyncSession):
    """Test generating a successful member statement."""
    # Arrange
    member_units = Decimal("150.12345678")
    mock_get_balance.return_value = member_units
    latest_unit_value = Decimal("11.50") # Value for the latest history point
    latest_valuation_date = date.today() # Assume latest history is today

    # FIX: Pass correct keyword arg 'valuation_date_for_initial'
    _creator, club, memberships, _funds, _positions, history = await setup_reporting_test_context(
        db_session,
        num_members=2,
        num_history_points=1, # Ensure at least one history point exists
        initial_unit_value=latest_unit_value,
        valuation_date_for_initial=latest_valuation_date # Use the correct keyword
    )
    target_membership = memberships[1] # Test for the second member created
    target_user_id = target_membership.user_id

    # Create some member transactions for this user
    tx1 = await create_test_member_transaction_via_crud(db_session, membership=target_membership, amount=Decimal("1000"))
    tx2 = await create_test_member_transaction_via_crud(db_session, membership=target_membership, amount=Decimal("575"))
    # Ensure relationships needed by MemberTransactionRead schema are loaded before validation
    await db_session.refresh(tx1, attribute_names=['membership'])
    await db_session.refresh(tx2, attribute_names=['membership'])
    # Need to load nested user/club within membership if schema requires it
    await db_session.refresh(target_membership, attribute_names=['user', 'club'])
    await db_session.refresh(tx1.membership, attribute_names=['user', 'club'])
    await db_session.refresh(tx2.membership, attribute_names=['user', 'club'])


    # Act
    print("Attempting manual rebuild for MemberStatementData in test...")
    try:
        # Import the specific schemas needed for rebuild within the test scope
        from backend.schemas.reporting import MemberStatementData
        from backend.schemas.member_transaction import MemberTransactionRead
        from backend.schemas.user import UserReadBasic
        from backend.schemas.club import ClubReadBasic
        MemberStatementData.model_rebuild(force=True)
        # Also rebuild the nested one just in case
        MemberTransactionRead.model_rebuild(force=True)
        print("MemberStatementData/MemberTransactionRead rebuild successful in test.")
    except Exception as e:
        print(f"MemberStatementData/MemberTransactionRead rebuild failed in test: {e}")
    statement = await reporting_service.get_member_statement(db=db_session, club_id=club.id, user_id=target_user_id)

    # Assert
    assert isinstance(statement, MemberStatementData)
    assert statement.club_id == club.id
    assert statement.user_id == target_user_id
    assert statement.membership_id == target_membership.id
    assert statement.statement_date == date.today()
    assert statement.current_unit_balance == member_units
    assert statement.latest_unit_value == latest_unit_value
    expected_equity = (member_units * latest_unit_value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    assert statement.current_equity_value == pytest.approx(expected_equity)
    assert len(statement.transactions) == 2
    tx_ids_in_statement = {tx.id for tx in statement.transactions}
    assert tx1.id in tx_ids_in_statement
    assert tx2.id in tx_ids_in_statement

    # Check mock call
    mock_get_balance.assert_called_once_with(db=db_session, membership_id=target_membership.id)


async def test_get_member_statement_membership_not_found(db_session: AsyncSession):
    """Test statement generation fails if membership doesn't exist."""
    # FIX: Correctly unpack the return value from the helper (6 items)
    _creator, club, _memberships, _funds, _positions, _history = await setup_reporting_test_context(db_session)
    non_member_user_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await reporting_service.get_member_statement(db=db_session, club_id=club.id, user_id=non_member_user_id)
    assert exc_info.value.status_code == 404
    assert "Membership for user" in exc_info.value.detail


# --- Tests for get_club_performance ---

async def test_get_club_performance_success(db_session: AsyncSession):
    """Test successful calculation of holding period return."""
    # Arrange
    num_history = 5
    _creator, club, _m, _f, _p, history = await setup_reporting_test_context(db_session, num_history_points=num_history)
    # Ensure history is sorted by date if helper doesn't guarantee it
    history.sort(key=lambda h: h.valuation_date)
    start_date = history[0].valuation_date
    end_date = history[-1].valuation_date
    start_value = history[0].unit_value
    end_value = history[-1].unit_value

    expected_hpr = float((end_value / start_value) - Decimal("1.0")) if start_value is not None and start_value > 0 else None

    # Act
    performance = await reporting_service.get_club_performance(
        db=db_session, club_id=club.id, start_date=start_date, end_date=end_date
    )

    # Assert
    assert isinstance(performance, ClubPerformanceData)
    assert performance.club_id == club.id
    assert performance.start_date == start_date
    assert performance.end_date == end_date
    assert performance.start_unit_value == start_value
    assert performance.end_unit_value == end_value
    if expected_hpr is not None:
        assert performance.holding_period_return == pytest.approx(expected_hpr)
    else:
        assert performance.holding_period_return is None


async def test_get_club_performance_no_history_in_range(db_session: AsyncSession):
    """Test performance calculation when no history exists in the date range."""
    _creator, club, _m, _f, _p, _history = await setup_reporting_test_context(db_session, num_history_points=1) # Only today's history
    start_date = date.today() - timedelta(days=10)
    end_date = date.today() - timedelta(days=5)

    # Act
    performance = await reporting_service.get_club_performance(
        db=db_session, club_id=club.id, start_date=start_date, end_date=end_date
    )

    # Assert
    assert performance.start_unit_value is None
    assert performance.end_unit_value is None
    assert performance.holding_period_return is None


async def test_get_club_performance_invalid_dates(db_session: AsyncSession):
    """Test performance calculation fails if start_date > end_date."""
    _creator, club, _m, _f, _p, _history = await setup_reporting_test_context(db_session)
    start_date = date.today()
    end_date = date.today() - timedelta(days=1)

    with pytest.raises(HTTPException) as exc_info:
        await reporting_service.get_club_performance(
            db=db_session, club_id=club.id, start_date=start_date, end_date=end_date
        )
    assert exc_info.value.status_code == 400
    assert "Start date cannot be after end date" in exc_info.value.detail

