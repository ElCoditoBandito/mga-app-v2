# backend/tests/services/test_reporting_service.py

import pytest
import uuid
from decimal import Decimal, ROUND_HALF_UP, DivisionByZero
from datetime import date, datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock
from typing import List, Sequence, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, MissingGreenlet
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

# Service functions to test
from backend.services import reporting_service
# Import the response models defined within the service file
from backend.services.reporting_service import MemberStatementData, ClubPerformanceData
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
from backend.schemas import ClubPortfolio, MemberTransactionCreate, PositionRead, UnitValueHistoryRead, MemberTransactionRead

# Import Auth0 mocking fixtures
from backend.tests.auth_fixtures import mock_auth0_token_verification, mock_get_current_active_user, test_user

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio

# --- Helper Function to Setup Context ---

async def setup_reporting_test_context(
    db_session: AsyncSession,
    num_members: int = 1,
    num_funds: int = 1,
    num_positions_per_fund: int = 1,
    num_history_points: int = 1,
    initial_unit_value: Optional[Decimal] = None,
    valuation_date_for_initial: Optional[date] = None
) -> tuple[User, Club, List[ClubMembership], List[Fund], List[Position], List[UnitValueHistory]]:
    """Creates a more complex setup for reporting tests."""
    # Create creator user
    creator_data = {
        "email": f"rep_cr_{uuid.uuid4().hex[:4]}@test.com",
        "auth0_sub": f"auth0|rep_cr_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    creator = await crud_user.create_user(db=db_session, user_data=creator_data)
    await db_session.flush()
    
    # Create club
    club_data = {
        "name": f"ReportTestClub_{uuid.uuid4().hex[:6]}",
        "description": "Test club for reporting",
        "bank_account_balance": Decimal("1000.00"),
        "creator_id": creator.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    # Create admin membership
    admin_membership_data = {
        "user_id": creator.id,
        "club_id": club.id,
        "role": ClubRole.ADMIN
    }
    admin_membership = await crud_membership.create_club_membership(db=db_session, membership_data=admin_membership_data)
    await db_session.flush()
    
    # Create additional members
    memberships = [admin_membership]
    for i in range(num_members - 1):
        member_data = {
            "email": f"rep_mem{i}_{uuid.uuid4().hex[:4]}@test.com",
            "auth0_sub": f"auth0|rep_mem{i}_{uuid.uuid4().hex[:6]}",
            "is_active": True
        }
        member_user = await crud_user.create_user(db=db_session, user_data=member_data)
        await db_session.flush()
        
        member_membership_data = {
            "user_id": member_user.id,
            "club_id": club.id,
            "role": ClubRole.MEMBER
        }
        member_membership = await crud_membership.create_club_membership(db=db_session, membership_data=member_membership_data)
        await db_session.flush()
        
        memberships.append(member_membership)
    
    # Create funds, assets, and positions
    funds = []
    positions = []
    assets = []
    for i in range(num_funds):
        fund_data = {
            "club_id": club.id,
            "name": f"Report Fund {i+1}",
            "description": f"Fund {i+1} for reporting tests",
            "brokerage_cash_balance": Decimal("500.00") * (i + 1),
            "is_active": True
        }
        fund = await crud_fund.create_fund(db=db_session, fund_data=fund_data)
        await db_session.flush()
        funds.append(fund)
        
        real_symbols = ['IBM', 'AAPL', 'MSFT', 'GOOG'] # Define list of real symbols
        for j in range(num_positions_per_fund):
            asset_data = {
                "asset_type": AssetType.STOCK,
                "symbol": real_symbols[(i * num_positions_per_fund + j) % len(real_symbols)], # Cycle through real symbols
                "name": f"Report Test Stock {i}{j}",
                "currency": Currency.USD
            }
            asset = await crud_asset.create_asset(db=db_session, asset_data=asset_data)
            await db_session.flush()
            assets.append(asset)
            
            position_data = {
                "fund_id": fund.id,
                "asset_id": asset.id,
                "quantity": Decimal(10*(i+1)*(j+1)),
                "average_cost_basis": Decimal(5*(i+1)*(j+1)) # Use correct model attribute name
            }
            position = await crud_position.create_position(db=db_session, position_data=position_data)
            await db_session.flush()
            positions.append(position)
    
    # Create unit value history
    history = []
    base_unit_value = Decimal("10.0")
    base_total_value = Decimal("10000")
    base_total_units = Decimal("1000")
    
    # Create the initial unit value if provided
    temp_num_history_points = num_history_points
    if initial_unit_value is not None:
        val_date = valuation_date_for_initial or date.today() - timedelta(days=temp_num_history_points)
        if temp_num_history_points == 1 and val_date >= date.today():
            val_date = date.today() - timedelta(days=1)
        
        uvh_data = {
            "club_id": club.id,
            "valuation_date": val_date,
            "total_club_value": initial_unit_value * base_total_units,
            "total_units_outstanding": base_total_units,
            "unit_value": initial_unit_value
        }
        hist = await crud_unit_value.create_unit_value_history(db=db_session, uvh_data=uvh_data)
        await db_session.flush()
        history.append(hist)
        
        days_diff = (date.today() - val_date).days
        skip_iterations = days_diff - (num_history_points - 1)
        temp_num_history_points = max(0, num_history_points - skip_iterations - 1)
    
    # Create remaining history points
    for i in range(temp_num_history_points):
        hist_date = date.today() - timedelta(days=temp_num_history_points - 1 - i)
        if any(h.valuation_date == hist_date for h in history):
            continue
        
        unit_val = base_unit_value + Decimal(i) * Decimal("0.1")
        uvh_data = {
            "club_id": club.id,
            "valuation_date": hist_date,
            "total_club_value": base_total_value + Decimal(i*100),
            "total_units_outstanding": base_total_units + Decimal(i*10),
            "unit_value": unit_val
        }
        hist = await crud_unit_value.create_unit_value_history(db=db_session, uvh_data=uvh_data)
        await db_session.flush()
        history.append(hist)
    
    await db_session.flush()
    return creator, club, memberships, funds, positions, history


# --- Tests for get_club_portfolio_report ---

async def test_get_club_portfolio_report_success(db_session: AsyncSession):
    """Test generating a successful club portfolio report using actual CRUD functions."""
    # Arrange
    num_funds = 2
    num_pos_per_fund = 2
    
    # Use the setup helper
    _creator, club, _memberships, funds, positions, history = await setup_reporting_test_context(
        db_session, num_funds=num_funds, num_positions_per_fund=num_pos_per_fund, num_history_points=1
    )
    valuation_date = date.today()
    
    # Fetch the latest history record
    latest_hist_model = await crud_unit_value.get_latest_unit_value_for_club(db=db_session, club_id=club.id)
    assert latest_hist_model is not None
    
    # Refresh relationships on positions
    expected_asset_ids = set()
    for pos in positions:
        await db_session.refresh(pos, attribute_names=['asset', 'fund'])
        assert pos.asset is not None
        assert pos.fund is not None
        if pos.asset_id:
            expected_asset_ids.add(pos.asset_id)
        
        # Refresh club and funds
        await db_session.refresh(club)
        for f in funds:
            await db_session.refresh(f)
        expected_total_cash = club.bank_account_balance + sum(f.brokerage_cash_balance for f in funds) # Corrected indentation (aligned with outer loop)
        
        # Act
        report = await reporting_service.get_club_portfolio_report(
            db=db_session, club_id=club.id, valuation_date=valuation_date
        )
        
        # Assert
        assert isinstance(report, ClubPortfolio)
        assert report.club_id == club.id
        assert report.valuation_date == valuation_date
        assert report.total_market_value > Decimal("0.0")
        assert report.total_cash_value == pytest.approx(expected_total_cash.quantize(Decimal("0.01")))
        assert len(report.aggregated_positions) == num_funds * num_pos_per_fund
        assert report.recent_unit_value is not None
        assert report.recent_unit_value.unit_value == latest_hist_model.unit_value


async def test_get_club_portfolio_report_club_not_found(db_session: AsyncSession):
    """Test report generation fails if club doesn't exist."""
    non_existent_club_id = uuid.uuid4()
    
    with pytest.raises(HTTPException) as exc_info:
        await reporting_service.get_club_portfolio_report(db=db_session, club_id=non_existent_club_id)
    
    assert exc_info.value.status_code == 404


# --- Tests for get_member_statement ---

async def test_get_member_statement_success(db_session: AsyncSession):
    """Test generating a successful member statement using actual CRUD functions."""
    # Arrange
    latest_unit_value = Decimal("11.50")
    latest_valuation_date = date.today()
    
    # Set up test context
    _creator, club, memberships, _funds, _positions, history = await setup_reporting_test_context(
        db_session,
        num_members=2,
        num_history_points=1,
        initial_unit_value=latest_unit_value,
        valuation_date_for_initial=latest_valuation_date
    )
    target_membership = memberships[1]  # Test for the second member created
    target_user_id = target_membership.user_id
    
    # Create member transactions
    tx1_data = {
        "membership_id": target_membership.id,
        "transaction_type": MemberTransactionType.DEPOSIT,
        "amount": Decimal("1000.00"),
        "transaction_date": datetime.now(timezone.utc) - timedelta(days=5),
        "unit_value_used": Decimal("10.00"),
        "units_transacted": Decimal("100.00000000"),
        "notes": "Test deposit 1"
    }
    tx2_data = {
        "membership_id": target_membership.id,
        "transaction_type": MemberTransactionType.DEPOSIT,
        "amount": Decimal("575.00"),
        "transaction_date": datetime.now(timezone.utc) - timedelta(days=2),
        "unit_value_used": Decimal("11.50"),
        "units_transacted": Decimal("50.00000000"),
        "notes": "Test deposit 2"
    }
    tx1 = await crud_member_tx.create_member_transaction(db=db_session, member_tx_data=tx1_data)
    tx2 = await crud_member_tx.create_member_transaction(db=db_session, member_tx_data=tx2_data)
    await db_session.flush()
    
    # Refresh relationships
    await db_session.refresh(tx1, attribute_names=['membership'])
    await db_session.refresh(tx2, attribute_names=['membership'])
    await db_session.refresh(target_membership, attribute_names=['user', 'club'])
    # Removed potentially redundant refresh calls
    
    # Act
    statement = await reporting_service.get_member_statement(db=db_session, club_id=club.id, user_id=target_user_id)
    
    # Assert
    assert isinstance(statement, MemberStatementData)
    assert statement.club_id == club.id
    assert statement.user_id == target_user_id
    assert statement.membership_id == target_membership.id
    assert statement.statement_date == date.today()
    
    # The current unit balance should be the sum of the units from both transactions
    expected_units = Decimal("150.00000000")
    assert statement.current_unit_balance == expected_units
    
    assert statement.latest_unit_value == latest_unit_value
    expected_equity = (expected_units * latest_unit_value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    assert statement.current_equity_value == pytest.approx(expected_equity)
    
    assert len(statement.transactions) == 2
    tx_ids_in_statement = {tx.id for tx in statement.transactions}
    assert tx1.id in tx_ids_in_statement
    assert tx2.id in tx_ids_in_statement


async def test_get_member_statement_membership_not_found(db_session: AsyncSession):
    """Test statement generation fails if membership doesn't exist."""
    _creator, club, _memberships, _funds, _positions, _history = await setup_reporting_test_context(db_session)
    non_member_user_id = uuid.uuid4()
    
    with pytest.raises(HTTPException) as exc_info:
        await reporting_service.get_member_statement(db=db_session, club_id=club.id, user_id=non_member_user_id)
    
    assert exc_info.value.status_code == 404
    assert "Membership for user" in exc_info.value.detail


# --- Tests for get_club_performance ---

async def test_get_club_performance_success(db_session: AsyncSession):
    """Test successful calculation of holding period return using actual CRUD functions."""
    # Arrange
    num_history = 5
    _creator, club, _m, _f, _p, history = await setup_reporting_test_context(db_session, num_history_points=num_history)
    
    # Ensure history is sorted by date
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
    _creator, club, _m, _f, _p, _history = await setup_reporting_test_context(db_session, num_history_points=1)
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
