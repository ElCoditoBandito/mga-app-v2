# backend/tests/api/test_reporting_api.py

import pytest
import pytest_asyncio
import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock # Added for mocking
from typing import List, Dict, Optional, AsyncGenerator
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

# Import the FastAPI app instance
from backend.main import app

# Import schemas and models
from backend.schemas import ClubPortfolio, ClubPerformanceData, UnitValueHistoryRead, NavCalculationRequest # Added reporting schemas
from backend.models import (
    User as UserModel, Club as ClubModel, Fund as FundModel, Asset as AssetModel,
    Position as PositionModel, ClubMembership as MembershipModel,
    UnitValueHistory as UnitValueHistoryModel, MemberTransaction as MemberTransactionModel
)
from backend.models.enums import ClubRole, AssetType, Currency, MemberTransactionType

# Import CRUD functions for verification/setup
from backend.crud import (
    club as crud_club, fund as crud_fund, asset as crud_asset,
    position as crud_position, club_membership as crud_membership,
    user as crud_user, unit_value_history as crud_unit_value,
    member_transaction as crud_member_tx
)

# Import fixtures
from backend.tests.auth_fixtures import authenticated_user, test_user
from backend.tests.conftest import db_session
# Import fixtures from club tests for setup
from backend.tests.api.test_clubs_api import club_admin_user, club_member_user, club_with_admin_and_member

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio


# --- Test Fixture for API Client ---
@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an asynchronous test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

# --- Helper Fixture for Reporting Test Setup ---
@pytest_asyncio.fixture(scope="function")
async def setup_reporting_data(
    db_session: AsyncSession,
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
) -> tuple[ClubModel, FundModel, AssetModel, PositionModel, Optional[UnitValueHistoryModel]]:
    """
    Fixture to create a club, fund, asset, position.
    Optionally creates a unit value history record (can be None if testing first NAV calc).
    """
    club, admin_user, member_user = club_with_admin_and_member
    club.bank_account_balance = Decimal("1000.00")
    db_session.add(club)

    # Create fund
    fund = await crud_fund.create_fund(
        db_session,
        fund_data={"club_id": club.id, "name": "Report Fund", "brokerage_cash_balance": Decimal("5000.00")}
    )
    await db_session.flush()

    # Create asset
    asset = await crud_asset.create_asset(
        db_session,
        asset_data={"asset_type": AssetType.STOCK, "symbol": "REP", "name": "Report Stock", "currency": Currency.USD}
    )
    await db_session.flush()

    # Create position
    position = await crud_position.create_position(
        db_session,
        position_data={"fund_id": fund.id, "asset_id": asset.id, "quantity": Decimal("100"), "average_cost_basis": Decimal("50.00")}
    )
    await db_session.flush()

    # Create member transaction for the member user to give them units
    member_membership = await crud_membership.get_club_membership_by_user_and_club(db_session, user_id=member_user.id, club_id=club.id)
    # Give admin units too for total units calculation
    admin_membership = await crud_membership.get_club_membership_by_user_and_club(db_session, user_id=admin_user.id, club_id=club.id)

    await crud_member_tx.create_member_transaction(
        db_session,
        member_tx_data={
            "membership_id": member_membership.id,
            "transaction_type": MemberTransactionType.DEPOSIT,
            "amount": Decimal("1000"), "transaction_date": datetime.now(timezone.utc) - timedelta(days=5),
            "unit_value_used": Decimal("10.0"), "units_transacted": Decimal("100.0") # Member gets 100 units
        }
    )
    await crud_member_tx.create_member_transaction(
        db_session,
        member_tx_data={
            "membership_id": admin_membership.id,
            "transaction_type": MemberTransactionType.DEPOSIT,
            "amount": Decimal("9000"), "transaction_date": datetime.now(timezone.utc) - timedelta(days=6),
            "unit_value_used": Decimal("10.0"), "units_transacted": Decimal("900.0") # Admin gets 900 units
        }
    ) # Total units = 1000
    await db_session.flush()

    await db_session.refresh(club)
    await db_session.refresh(fund)
    await db_session.refresh(asset)
    await db_session.refresh(position)

    # Return None for history initially, let tests create specific history if needed
    return club, fund, asset, position, None

# --- Mock for Market Data ---
# Mock needs to patch the function called by the NAV calculation service
@pytest_asyncio.fixture(scope="function")
async def mock_nav_market_prices():
    """ Mocks the accounting_service.get_market_prices function used by NAV calc. """
    async def _mock_get_prices(db: AsyncSession, asset_ids: List[uuid.UUID], valuation_date: date) -> Dict[uuid.UUID, Decimal]:
        # Return a fixed price for any requested asset ID for simplicity
        mock_price = Decimal("65.00") # Example market price for NAV calc
        return {asset_id: mock_price for asset_id in asset_ids}

    # Patch the function within the accounting_service module
    with patch("backend.services.accounting_service.get_market_prices", new=_mock_get_prices) as mock:
        yield mock

# Mock for reporting service market data (can use different prices if needed)
@pytest_asyncio.fixture(scope="function")
async def mock_reporting_market_prices():
    """ Mocks the reporting_service.get_market_prices function used by reports. """
    async def _mock_get_prices(db: AsyncSession, asset_ids: List[uuid.UUID], valuation_date: date) -> Dict[uuid.UUID, Decimal]:
        mock_price = Decimal("70.00") # Different mock price for reporting tests
        return {asset_id: mock_price for asset_id in asset_ids}

    with patch("backend.services.reporting_service.get_market_prices", new=_mock_get_prices) as mock:
        yield mock


# --- API Tests for GET /clubs/{club_id}/portfolio ---

async def test_get_club_portfolio_success(
    client: AsyncClient,
    club_member_user: UserModel, # Requesting user
    setup_reporting_data: tuple[ClubModel, FundModel, AssetModel, PositionModel, Optional[UnitValueHistoryModel]],
    mock_reporting_market_prices: AsyncMock # Apply the reporting mock
):
    """Test successfully retrieving the club portfolio report."""
    # Arrange
    club, fund, asset, position, _ = setup_reporting_data # History not needed directly here
    member_user = club_member_user
    valuation_date = date.today()
    mock_price = Decimal("70.00") # Price from the reporting mock

    # Create a history record for the portfolio report to pick up
    latest_hist = await crud_unit_value.create_unit_value_history(
        db_session.object_session(club), # Use session from fixture object
        uvh_data={"club_id": club.id, "valuation_date": date.today() - timedelta(days=1), "total_club_value": 11000, "total_units_outstanding": 1000, "unit_value": 11.0}
    )
    await db_session.object_session(club).flush()


    expected_position_market_value = position.quantity * mock_price
    expected_total_market_value = expected_position_market_value
    expected_total_cash = club.bank_account_balance + fund.brokerage_cash_balance

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)

        # Act
        response = await client.get(f"/api/v1/clubs/{club.id}/portfolio?valuation_date={valuation_date.isoformat()}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        report_data = ClubPortfolio(**response.json())

        assert report_data.club_id == club.id
        assert report_data.valuation_date == valuation_date
        assert report_data.total_market_value == expected_total_market_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert report_data.total_cash_value == expected_total_cash.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert len(report_data.aggregated_positions) == 1
        assert report_data.aggregated_positions[0].id == position.id
        assert report_data.aggregated_positions[0].asset.id == asset.id
        assert report_data.recent_unit_value is not None
        assert report_data.recent_unit_value.id == latest_hist.id
        assert report_data.recent_unit_value.unit_value == latest_hist.unit_value

async def test_get_club_portfolio_unauthenticated(client: AsyncClient, setup_reporting_data):
    """Test getting portfolio fails without authentication."""
    club, _, _, _, _ = setup_reporting_data
    response = await client.get(f"/api/v1/clubs/{club.id}/portfolio")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_get_club_portfolio_not_member(
    client: AsyncClient,
    authenticated_user: UserModel, # User is authenticated but not member of club below
    setup_reporting_data: tuple[ClubModel, FundModel, AssetModel, PositionModel, Optional[UnitValueHistoryModel]]
):
    """Test getting portfolio fails if user is not a club member."""
    club, _, _, _, _ = setup_reporting_data
    non_member_user = authenticated_user

    # Mock authentication as non-member
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: non_member_user)
        # Act
        response = await client.get(f"/api/v1/clubs/{club.id}/portfolio")
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

# --- API Tests for GET /clubs/{club_id}/performance ---

async def test_get_club_performance_success(
    client: AsyncClient,
    db_session: AsyncSession,
    club_member_user: UserModel,
    setup_reporting_data: tuple[ClubModel, FundModel, AssetModel, PositionModel, Optional[UnitValueHistoryModel]]
):
    """Test successfully retrieving the club performance report."""
    # Arrange
    club, _, _, _, _ = setup_reporting_data # Initial history not created by fixture
    member_user = club_member_user

    # Create history points
    hist0_date = date.today() - timedelta(days=10)
    hist0_value = Decimal("10.00000000")
    hist0 = await crud_unit_value.create_unit_value_history(
        db_session,
        uvh_data={"club_id": club.id, "valuation_date": hist0_date, "total_club_value": 10000, "total_units_outstanding": 1000, "unit_value": hist0_value}
    )
    hist1_date = date.today() - timedelta(days=1)
    hist1_value = Decimal("11.00000000")
    hist1 = await crud_unit_value.create_unit_value_history(
        db_session,
        uvh_data={"club_id": club.id, "valuation_date": hist1_date, "total_club_value": 11000, "total_units_outstanding": 1000, "unit_value": hist1_value}
    )
    await db_session.flush()

    start_date = hist0_date
    end_date = hist1_date
    expected_hpr = float((hist1.unit_value / hist0_value) - Decimal("1.0"))

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)

        # Act
        response = await client.get(f"/api/v1/clubs/{club.id}/performance?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        perf_data = ClubPerformanceData(**response.json())

        assert perf_data.club_id == club.id
        assert perf_data.start_date == start_date
        assert perf_data.end_date == end_date
        assert perf_data.start_unit_value == hist0_value
        assert perf_data.end_unit_value == hist1_value
        assert perf_data.holding_period_return == pytest.approx(expected_hpr)

async def test_get_club_performance_invalid_dates(
    client: AsyncClient,
    club_member_user: UserModel,
    setup_reporting_data: tuple[ClubModel, FundModel, AssetModel, PositionModel, Optional[UnitValueHistoryModel]]
):
    """Test performance report fails if start_date > end_date."""
    club, _, _, _, _ = setup_reporting_data
    member_user = club_member_user
    start_date = date.today()
    end_date = date.today() - timedelta(days=1)

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)
        # Act
        response = await client.get(f"/api/v1/clubs/{club.id}/performance?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}")
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Start date cannot be after end date" in response.json()["detail"]

async def test_get_club_performance_unauthenticated(client: AsyncClient, setup_reporting_data):
    """Test getting performance fails without authentication."""
    club, _, _, _, _ = setup_reporting_data
    start_date = date.today() - timedelta(days=10)
    end_date = date.today()
    response = await client.get(f"/api/v1/clubs/{club.id}/performance?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_get_club_performance_not_member(
    client: AsyncClient,
    authenticated_user: UserModel, # User is authenticated but not member of club below
    setup_reporting_data: tuple[ClubModel, FundModel, AssetModel, PositionModel, Optional[UnitValueHistoryModel]]
):
    """Test getting performance fails if user is not a club member."""
    club, _, _, _, _ = setup_reporting_data
    non_member_user = authenticated_user
    start_date = date.today() - timedelta(days=10)
    end_date = date.today()

    # Mock authentication as non-member
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: non_member_user)
        # Act
        response = await client.get(f"/api/v1/clubs/{club.id}/performance?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}")
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN

# --- API Tests for POST /clubs/{club_id}/calculate-nav ---

async def test_calculate_nav_success(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_reporting_data: tuple[ClubModel, FundModel, AssetModel, PositionModel, Optional[UnitValueHistoryModel]],
    mock_nav_market_prices: AsyncMock # Apply the NAV mock
):
    """Test successfully triggering NAV calculation by an admin."""
    # Arrange
    club, fund, asset, position, _ = setup_reporting_data
    admin_user = club_admin_user
    valuation_date = date.today()
    mock_price = Decimal("65.00") # Price from the NAV mock

    # Expected calculations based on fixture data and mock price
    expected_market_value = position.quantity * mock_price # 100 * 65 = 6500
    expected_cash = club.bank_account_balance + fund.brokerage_cash_balance # 1000 + 5000 = 6000
    expected_total_value = expected_market_value + expected_cash # 6500 + 6000 = 12500
    expected_total_units = Decimal("1000.00000000") # From fixture setup (100 + 900)
    expected_unit_value = (expected_total_value / expected_total_units).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP) # 12500 / 1000 = 12.5

    request_body = NavCalculationRequest(valuation_date=valuation_date)

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)

        # Act
        response = await client.post(f"/api/v1/clubs/{club.id}/calculate-nav", json=request_body.model_dump(mode='json'))

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED
        nav_history = UnitValueHistoryRead(**response.json())
        assert nav_history.club_id == club.id
        assert nav_history.valuation_date == valuation_date
        assert nav_history.total_club_value == expected_total_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert nav_history.total_units_outstanding == expected_total_units
        assert nav_history.unit_value == expected_unit_value

    # Assert Database State
    db_hist = await crud_unit_value.get_unit_value_history(db_session, nav_history.id)
    assert db_hist is not None
    assert db_hist.valuation_date == valuation_date
    assert db_hist.unit_value == expected_unit_value


async def test_calculate_nav_forbidden_by_member(
    client: AsyncClient,
    club_member_user: UserModel,
    setup_reporting_data: tuple[ClubModel, FundModel, AssetModel, PositionModel, Optional[UnitValueHistoryModel]],
    mock_nav_market_prices: AsyncMock
):
    """Test triggering NAV calculation fails for a non-admin member."""
    # Arrange
    club, _, _, _, _ = setup_reporting_data
    member_user = club_member_user
    valuation_date = date.today()
    request_body = NavCalculationRequest(valuation_date=valuation_date)

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)
        # Act
        response = await client.post(f"/api/v1/clubs/{club.id}/calculate-nav", json=request_body.model_dump(mode='json'))
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_calculate_nav_unauthenticated(
    client: AsyncClient,
    setup_reporting_data: tuple[ClubModel, FundModel, AssetModel, PositionModel, Optional[UnitValueHistoryModel]]
):
    """Test triggering NAV calculation fails without authentication."""
    # Arrange
    club, _, _, _, _ = setup_reporting_data
    valuation_date = date.today()
    request_body = NavCalculationRequest(valuation_date=valuation_date)
    # Act
    response = await client.post(f"/api/v1/clubs/{club.id}/calculate-nav", json=request_body.model_dump(mode='json'))
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_calculate_nav_conflict_duplicate_date(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_reporting_data: tuple[ClubModel, FundModel, AssetModel, PositionModel, Optional[UnitValueHistoryModel]],
    mock_nav_market_prices: AsyncMock
):
    """Test triggering NAV calculation fails if record for date already exists."""
    # Arrange
    club, _, _, _, _ = setup_reporting_data
    admin_user = club_admin_user
    valuation_date = date.today()

    # Create an existing record for today
    await crud_unit_value.create_unit_value_history(
        db_session,
        uvh_data={"club_id": club.id, "valuation_date": valuation_date, "total_club_value": 1, "total_units_outstanding": 1, "unit_value": 1}
    )
    await db_session.flush()

    request_body = NavCalculationRequest(valuation_date=valuation_date)

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act
        response = await client.post(f"/api/v1/clubs/{club.id}/calculate-nav", json=request_body.model_dump(mode='json'))
        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"]

