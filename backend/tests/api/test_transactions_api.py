# backend/tests/api/test_transactions_api.py

import pytest
import pytest_asyncio
import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, date, timedelta # Added timedelta
from typing import List, Optional, Sequence, AsyncGenerator # Added Sequence
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

# Import the FastAPI app instance
from backend.main import app

# Import schemas and models
from backend.schemas import ( # Added TransactionCreateOptionLifecycle
    TransactionCreateTrade, TransactionRead,
    TransactionCreateDividendBrokerageInterest, TransactionCreateCashTransfer,
    TransactionCreateOptionLifecycle
)
from backend.models import User as UserModel, Club as ClubModel, Fund as FundModel, Asset as AssetModel, Position as PositionModel, ClubMembership as MembershipModel, FundSplit as FundSplitModel, Transaction as TransactionModel # Added TransactionModel
from backend.models.enums import ClubRole, AssetType, TransactionType, Currency, OptionType # Added OptionType

# Import CRUD functions for verification/setup
from backend.crud import club as crud_club
from backend.crud import fund as crud_fund
from backend.crud import asset as crud_asset
from backend.crud import position as crud_position
from backend.crud import club_membership as crud_membership
from backend.crud import user as crud_user
from backend.crud import fund_split as crud_fund_split
from backend.crud import transaction as crud_transaction # Added transaction crud

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

# --- Helper Fixtures for Test Setup ---
@pytest_asyncio.fixture(scope="function")
async def setup_fund_and_asset(db_session: AsyncSession, club_with_admin_and_member) -> tuple[ClubModel, FundModel, AssetModel]:
    """Fixture to create a club, fund, and a stock asset for trade tests."""
    club, admin_user, _ = club_with_admin_and_member

    # Create a fund within the club with some initial cash
    fund = await crud_fund.create_fund(
        db_session,
        fund_data={
            "club_id": club.id,
            "name": "Trading Fund",
            "brokerage_cash_balance": Decimal("10000.00"),
            "is_active": True
        }
    )
    await db_session.flush()

    # Create a stock asset
    asset = await crud_asset.create_asset(
        db_session,
        asset_data={
            "asset_type": AssetType.STOCK,
            "symbol": "TEST",
            "name": "Test Stock Inc.",
            "currency": Currency.USD
        }
    )
    await db_session.flush()
    await db_session.refresh(fund)
    await db_session.refresh(asset)
    await db_session.refresh(club) # Refresh club too

    return club, fund, asset

@pytest_asyncio.fixture(scope="function")
async def setup_multiple_funds(db_session: AsyncSession, club_with_admin_and_member) -> tuple[ClubModel, FundModel, FundModel]:
    """Fixture to create a club with two funds for transfer tests."""
    club, admin_user, _ = club_with_admin_and_member
    club.bank_account_balance = Decimal("50000.00") # Give club bank some cash
    db_session.add(club)

    # Create two funds
    fund1 = await crud_fund.create_fund(
        db_session,
        fund_data={"club_id": club.id, "name": "Fund Alpha", "brokerage_cash_balance": Decimal("1000.00"), "is_active": True}
    )
    fund2 = await crud_fund.create_fund(
        db_session,
        fund_data={"club_id": club.id, "name": "Fund Beta", "brokerage_cash_balance": Decimal("500.00"), "is_active": True}
    )
    await db_session.flush()
    await db_session.refresh(club)
    await db_session.refresh(fund1)
    await db_session.refresh(fund2)
    return club, fund1, fund2

@pytest_asyncio.fixture(scope="function")
async def setup_option_position(
    db_session: AsyncSession,
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
) -> tuple[ClubModel, FundModel, AssetModel, AssetModel, PositionModel]:
    """
    Fixture to create a club, fund, underlying stock, an option asset,
    and a LONG position in that option.
    """
    club, fund, underlying_asset = setup_fund_and_asset

    # Create an option asset (e.g., a CALL)
    strike_price = Decimal("100.00")
    expiration_date = date.today() + timezone.timedelta(days=30)
    option_asset = await crud_asset.create_asset(
        db_session,
        asset_data={
            "asset_type": AssetType.OPTION,
            "symbol": f"{underlying_asset.symbol}_{expiration_date.strftime('%y%m%d')}C{int(strike_price)}",
            "name": f"{underlying_asset.symbol} {expiration_date.strftime('%b %d %Y')} ${strike_price:.2f} Call",
            "currency": underlying_asset.currency,
            "underlying_asset_id": underlying_asset.id,
            "option_type": OptionType.CALL,
            "strike_price": strike_price,
            "expiration_date": expiration_date
        }
    )
    await db_session.flush()

    # Create a LONG position in the option (e.g., bought 5 contracts)
    option_position = await crud_position.create_position(
        db_session,
        position_data={
            "fund_id": fund.id,
            "asset_id": option_asset.id,
            "quantity": Decimal("5.0"), # Long 5 contracts
            "average_cost_basis": Decimal("2.50") # Example cost basis per contract
        }
    )
    await db_session.flush()
    await db_session.refresh(option_asset, attribute_names=['underlying_asset']) # Ensure relationship loaded
    await db_session.refresh(option_position, attribute_names=['asset', 'fund'])

    return club, fund, underlying_asset, option_asset, option_position

@pytest_asyncio.fixture(scope="function")
async def setup_multiple_transactions(
    db_session: AsyncSession,
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
) -> tuple[ClubModel, FundModel, AssetModel, List[TransactionModel]]:
    """Fixture to create multiple transactions within a fund."""
    club, fund, asset = setup_fund_and_asset
    transactions = []
    now = datetime.now(timezone.utc)

    # Create a BUY transaction
    tx_buy_data = {"fund_id": fund.id, "asset_id": asset.id, "transaction_type": TransactionType.BUY_STOCK, "transaction_date": now - timedelta(days=2), "quantity": Decimal("10"), "price_per_unit": Decimal("90")}
    tx_buy = await crud_transaction.create_transaction(db_session, transaction_data=tx_buy_data)
    transactions.append(tx_buy)

    # Create a DIVIDEND transaction
    tx_div_data = {"fund_id": fund.id, "asset_id": asset.id, "transaction_type": TransactionType.DIVIDEND, "transaction_date": now - timedelta(days=1), "total_amount": Decimal("20")}
    tx_div = await crud_transaction.create_transaction(db_session, transaction_data=tx_div_data)
    transactions.append(tx_div)

    # Create a SELL transaction
    tx_sell_data = {"fund_id": fund.id, "asset_id": asset.id, "transaction_type": TransactionType.SELL_STOCK, "transaction_date": now, "quantity": Decimal("5"), "price_per_unit": Decimal("110")}
    tx_sell = await crud_transaction.create_transaction(db_session, transaction_data=tx_sell_data)
    transactions.append(tx_sell)

    # Create a transaction in another fund/club (should not be listed)
    other_user = await crud_user.create_user(db_session, user_data={"email": f"tx_other_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|tx_other_{uuid.uuid4()}"})
    await db_session.flush()
    other_club = await crud_club.create_club(db_session, club_data={"name": f"Other Tx Club {uuid.uuid4()}", "creator_id": other_user.id})
    await db_session.flush()
    other_fund = await crud_fund.create_fund(db_session, fund_data={"club_id": other_club.id, "name": "Other Fund"})
    await db_session.flush()
    other_asset = await crud_asset.create_asset(db_session, asset_data={"asset_type": AssetType.STOCK, "symbol": "OTHER", "currency": Currency.USD})
    await db_session.flush()
    other_tx_data = {"fund_id": other_fund.id, "asset_id": other_asset.id, "transaction_type": TransactionType.BUY_STOCK, "transaction_date": now, "quantity": Decimal("100"), "price_per_unit": Decimal("10")}
    await crud_transaction.create_transaction(db_session, transaction_data=other_tx_data)

    await db_session.flush()
    # Refresh main objects
    await db_session.refresh(club)
    await db_session.refresh(fund)
    await db_session.refresh(asset)
    for tx in transactions:
        await db_session.refresh(tx)

    # Sort transactions by date desc for expected order
    transactions.sort(key=lambda t: t.transaction_date, reverse=True)

    return club, fund, asset, transactions
# --- API Tests for POST /transactions/trade ---

async def test_record_trade_buy_stock_success(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel, # Authenticated admin user
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test successfully recording a BUY_STOCK trade by an admin."""
    # Arrange
    club, fund, asset = setup_fund_and_asset
    admin_user = club_admin_user # User making the request
    initial_fund_cash = fund.brokerage_cash_balance

    trade_data = TransactionCreateTrade(
        fund_id=fund.id,
        asset_id=asset.id,
        transaction_type=TransactionType.BUY_STOCK,
        quantity=Decimal("50"),
        price_per_unit=Decimal("150.00"),
        fees_commissions=Decimal("5.00"),
        transaction_date=datetime.now(timezone.utc),
        description="API Test Buy Stock"
    )
    expected_cost = (trade_data.quantity * trade_data.price_per_unit) + trade_data.fees_commissions
    expected_final_cash = initial_fund_cash - expected_cost

    # Mock authentication as the admin user
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)

        # Act
        # Pass club_id in query param due to routing inconsistency
        response = await client.post(f"/api/v1/transactions/trade?club_id={club.id}", json=trade_data.model_dump(mode='json'))

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        tx_response = TransactionRead(**response_data)

        assert tx_response.fund_id == fund.id
        assert tx_response.asset_id == asset.id
        assert tx_response.transaction_type == TransactionType.BUY_STOCK
        assert tx_response.quantity == trade_data.quantity
        assert tx_response.price_per_unit == trade_data.price_per_unit
        assert tx_response.fees_commissions == trade_data.fees_commissions
        assert tx_response.id is not None

    # Assert Database State (outside monkeypatch context)
    await db_session.refresh(fund) # Refresh fund to get updated balance
    assert fund.brokerage_cash_balance == expected_final_cash

    position = await crud_position.get_position_by_fund_and_asset(db=db_session, fund_id=fund.id, asset_id=asset.id)
    assert position is not None
    assert position.quantity == trade_data.quantity
    assert position.average_cost_basis == trade_data.price_per_unit # First buy


async def test_record_trade_forbidden_by_member(
    client: AsyncClient,
    club_member_user: UserModel, # Authenticated member user
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test recording a trade fails when attempted by a non-admin member."""
    # Arrange
    club, fund, asset = setup_fund_and_asset
    member_user = club_member_user # User making the request

    trade_data = TransactionCreateTrade(
        fund_id=fund.id,
        asset_id=asset.id,
        transaction_type=TransactionType.BUY_STOCK,
        quantity=Decimal("10"),
        price_per_unit=Decimal("100.00"),
        transaction_date=datetime.now(timezone.utc)
    )

    # Mock authentication as the member user
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)

        # Act
        response = await client.post(f"/api/v1/transactions/trade?club_id={club.id}", json=trade_data.model_dump(mode='json')) # Pass club_id

        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_record_trade_unauthenticated(
    client: AsyncClient,
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test recording a trade fails without authentication."""
    # Arrange
    club, fund, asset = setup_fund_and_asset
    trade_data = TransactionCreateTrade(
        fund_id=fund.id,
        asset_id=asset.id,
        transaction_type=TransactionType.BUY_STOCK,
        quantity=Decimal("10"),
        price_per_unit=Decimal("100.00"),
        transaction_date=datetime.now(timezone.utc)
    )

    # Act
    response = await client.post(f"/api/v1/transactions/trade?club_id={club.id}", json=trade_data.model_dump(mode='json')) # Pass club_id

    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_record_trade_insufficient_funds(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel, # Authenticated admin user
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test recording a buy trade fails due to insufficient funds."""
    # Arrange
    club, fund, asset = setup_fund_and_asset
    admin_user = club_admin_user

    # Set fund cash low deliberately
    fund.brokerage_cash_balance = Decimal("100.00")
    db_session.add(fund)
    await db_session.flush()
    await db_session.refresh(fund)

    trade_data = TransactionCreateTrade(
        fund_id=fund.id,
        asset_id=asset.id,
        transaction_type=TransactionType.BUY_STOCK,
        quantity=Decimal("10"), # Cost = 10 * 20 = 200
        price_per_unit=Decimal("20.00"),
        fees_commissions=Decimal("1.00"), # Total needed = 201
        transaction_date=datetime.now(timezone.utc)
    )

    # Mock authentication as the admin user
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)

        # Act
        response = await client.post(f"/api/v1/transactions/trade?club_id={club.id}", json=trade_data.model_dump(mode='json')) # Pass club_id

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient funds" in response.json()["detail"]

    # Assert Database State (ensure balance didn't change)
    await db_session.refresh(fund)
    assert fund.brokerage_cash_balance == Decimal("100.00")


async def test_record_trade_invalid_data(
    client: AsyncClient,
    club_admin_user: UserModel,
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test recording a trade fails with invalid data (e.g., negative quantity)."""
    # Arrange
    club, fund, asset = setup_fund_and_asset
    admin_user = club_admin_user

    invalid_trade_data = { # Using dict to bypass Pydantic validation initially
        "fund_id": str(fund.id), # Ensure UUIDs are strings for JSON
        "asset_id": str(asset.id),
        "transaction_type": TransactionType.BUY_STOCK.value,
        "quantity": "-10", # Invalid quantity
        "price_per_unit": "100.00",
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }

    # Mock authentication as the admin user
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)

        # Act
        response = await client.post(f"/api/v1/transactions/trade?club_id={club.id}", json=invalid_trade_data) # Pass club_id

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_record_trade_fund_mismatch(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test recording a trade fails if fund_id in body doesn't belong to club_id in path."""
    # Arrange
    club1, fund1, asset1 = setup_fund_and_asset
    admin_user = club_admin_user

    # Create a second club and fund
    other_club_creator = await crud_user.create_user(db_session, user_data={"email": f"other_c_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|other_c_{uuid.uuid4()}"})
    await db_session.flush()
    club2 = await crud_club.create_club(db_session, club_data={"name": "Club Two", "creator_id": other_club_creator.id})
    await db_session.flush()
    fund2 = await crud_fund.create_fund(db_session, fund_data={"club_id": club2.id, "name": "Fund Two"})
    await db_session.flush()

    trade_data = TransactionCreateTrade(
        fund_id=fund2.id, # Fund from club2
        asset_id=asset1.id, # Asset doesn't matter here
        transaction_type=TransactionType.BUY_STOCK,
        quantity=Decimal("1"),
        price_per_unit=Decimal("1"),
        transaction_date=datetime.now(timezone.utc)
    )

    # Mock authentication as admin of club1
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)

        # Act: Try to post to club1's endpoint but with fund_id from club2
        response = await client.post(f"/api/v1/transactions/trade?club_id={club1.id}", json=trade_data.model_dump(mode='json'))

        # Assert: Should be forbidden because fund doesn't belong to club in path
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert f"Fund {fund2.id} does not belong to club {club1.id}" in response.json()["detail"]

# --- API Tests for POST /transactions/cash-receipt ---

async def test_record_cash_receipt_dividend_success(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test successfully recording a DIVIDEND cash receipt by an admin."""
    # Arrange
    club, fund, asset = setup_fund_and_asset
    admin_user = club_admin_user
    initial_fund_cash = fund.brokerage_cash_balance
    dividend_amount = Decimal("55.25")

    receipt_data = TransactionCreateDividendBrokerageInterest(
        fund_id=fund.id,
        asset_id=asset.id, # Required for dividend
        transaction_type=TransactionType.DIVIDEND,
        total_amount=dividend_amount,
        transaction_date=datetime.now(timezone.utc),
        description="API Test Dividend"
    )
    expected_final_cash = initial_fund_cash + dividend_amount

    # Mock authentication as admin
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)

        # Act
        response = await client.post(f"/api/v1/transactions/cash-receipt?club_id={club.id}", json=receipt_data.model_dump(mode='json'))

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED
        tx_response = TransactionRead(**response.json())
        assert tx_response.fund_id == fund.id
        assert tx_response.asset_id == asset.id
        assert tx_response.transaction_type == TransactionType.DIVIDEND
        assert tx_response.total_amount == dividend_amount
        assert tx_response.fees_commissions == Decimal("0.00") # Default

    # Assert Database State
    await db_session.refresh(fund)
    assert fund.brokerage_cash_balance == expected_final_cash


async def test_record_cash_receipt_interest_success(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test successfully recording BROKERAGE_INTEREST cash receipt by an admin."""
    # Arrange
    club, fund, _ = setup_fund_and_asset # Asset not needed for interest
    admin_user = club_admin_user
    initial_fund_cash = fund.brokerage_cash_balance
    interest_amount = Decimal("12.34")

    receipt_data = TransactionCreateDividendBrokerageInterest(
        fund_id=fund.id,
        asset_id=None, # Must be None for interest
        transaction_type=TransactionType.BROKERAGE_INTEREST,
        total_amount=interest_amount,
        transaction_date=datetime.now(timezone.utc),
        description="API Test Interest"
    )
    expected_final_cash = initial_fund_cash + interest_amount

    # Mock authentication as admin
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)

        # Act
        response = await client.post(f"/api/v1/transactions/cash-receipt?club_id={club.id}", json=receipt_data.model_dump(mode='json'))

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED
        tx_response = TransactionRead(**response.json())
        assert tx_response.fund_id == fund.id
        assert tx_response.asset_id is None
        assert tx_response.transaction_type == TransactionType.BROKERAGE_INTEREST
        assert tx_response.total_amount == interest_amount

    # Assert Database State
    await db_session.refresh(fund)
    assert fund.brokerage_cash_balance == expected_final_cash


async def test_record_cash_receipt_forbidden_by_member(
    client: AsyncClient,
    club_member_user: UserModel,
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test recording a cash receipt fails when attempted by a non-admin member."""
    # Arrange
    club, fund, asset = setup_fund_and_asset
    member_user = club_member_user

    receipt_data = TransactionCreateDividendBrokerageInterest(
        fund_id=fund.id,
        asset_id=asset.id,
        transaction_type=TransactionType.DIVIDEND,
        total_amount=Decimal("10.00")
    )

    # Mock authentication as member
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)
        # Act
        response = await client.post(f"/api/v1/transactions/cash-receipt?club_id={club.id}", json=receipt_data.model_dump(mode='json'))
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_record_cash_receipt_unauthenticated(
    client: AsyncClient,
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test recording a cash receipt fails without authentication."""
    # Arrange
    club, fund, asset = setup_fund_and_asset
    receipt_data = TransactionCreateDividendBrokerageInterest(
        fund_id=fund.id,
        asset_id=asset.id,
        transaction_type=TransactionType.DIVIDEND,
        total_amount=Decimal("10.00")
    )
    # Act
    response = await client.post(f"/api/v1/transactions/cash-receipt?club_id={club.id}", json=receipt_data.model_dump(mode='json'))
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_record_cash_receipt_dividend_missing_asset(
    client: AsyncClient,
    club_admin_user: UserModel,
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test recording a dividend fails if asset_id is missing."""
    # Arrange
    club, fund, _ = setup_fund_and_asset
    admin_user = club_admin_user

    invalid_receipt_data = { # Use dict to bypass Pydantic validation initially
        "fund_id": str(fund.id),
        # "asset_id": None, # Missing asset_id
        "transaction_type": TransactionType.DIVIDEND.value,
        "total_amount": "50.00",
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }

    # Mock authentication as admin
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act
        response = await client.post(f"/api/v1/transactions/cash-receipt?club_id={club.id}", json=invalid_receipt_data)
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Check detail message indicates asset_id is required for DIVIDEND
        assert "asset_id" in response.json()["detail"][0]["loc"]
        assert "Field 'asset_id' is required" in response.json()["detail"][0]["msg"]


async def test_record_cash_receipt_interest_with_asset(
    client: AsyncClient,
    club_admin_user: UserModel,
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test recording brokerage interest fails if asset_id is provided."""
    # Arrange
    club, fund, asset = setup_fund_and_asset
    admin_user = club_admin_user

    invalid_receipt_data = { # Use dict to bypass Pydantic validation initially
        "fund_id": str(fund.id),
        "asset_id": str(asset.id), # Incorrectly provided asset_id
        "transaction_type": TransactionType.BROKERAGE_INTEREST.value,
        "total_amount": "15.00",
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }

    # Mock authentication as admin
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act
        response = await client.post(f"/api/v1/transactions/cash-receipt?club_id={club.id}", json=invalid_receipt_data)
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Check detail message indicates asset_id must be null for BROKERAGE_INTEREST
        assert "asset_id" in response.json()["detail"][0]["loc"]
        assert "Field 'asset_id' must be null" in response.json()["detail"][0]["msg"]


async def test_record_cash_receipt_fund_mismatch(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_fund_and_asset: tuple[ClubModel, FundModel, AssetModel]
):
    """Test recording cash receipt fails if fund_id in body doesn't belong to club_id in path."""
    # Arrange
    club1, fund1, asset1 = setup_fund_and_asset
    admin_user = club_admin_user

    # Create a second club and fund
    other_club_creator = await crud_user.create_user(db_session, user_data={"email": f"other_cr_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|other_cr_{uuid.uuid4()}"})
    await db_session.flush()
    club2 = await crud_club.create_club(db_session, club_data={"name": "Club Tres", "creator_id": other_club_creator.id})
    await db_session.flush()
    fund2 = await crud_fund.create_fund(db_session, fund_data={"club_id": club2.id, "name": "Fund Tres"})
    await db_session.flush()

    receipt_data = TransactionCreateDividendBrokerageInterest(
        fund_id=fund2.id, # Fund from club2
        asset_id=asset1.id, # Asset doesn't matter here
        transaction_type=TransactionType.DIVIDEND,
        total_amount=Decimal("10.00")
    )

    # Mock authentication as admin of club1
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)

        # Act: Try to post to club1's endpoint but with fund_id from club2
        response = await client.post(f"/api/v1/transactions/cash-receipt?club_id={club1.id}", json=receipt_data.model_dump(mode='json'))

        # Assert: Should be forbidden because fund doesn't belong to club in path
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert f"Fund {fund2.id} does not belong to club {club1.id}" in response.json()["detail"]

# --- API Tests for POST /transactions/cash-transfer ---

async def test_record_cash_transfer_bank_to_brokerage_split_success(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_multiple_funds: tuple[ClubModel, FundModel, FundModel]
):
    """Test successful BANK_TO_BROKERAGE transfer with fund splits."""
    # Arrange
    club, fund1, fund2 = setup_multiple_funds
    admin_user = club_admin_user
    initial_bank_balance = club.bank_account_balance
    initial_fund1_cash = fund1.brokerage_cash_balance
    initial_fund2_cash = fund2.brokerage_cash_balance

    # Create fund splits (60/40)
    await crud_fund_split.create_fund_split(db_session, fund_split_data={"club_id": club.id, "fund_id": fund1.id, "split_percentage": Decimal("0.6")})
    await crud_fund_split.create_fund_split(db_session, fund_split_data={"club_id": club.id, "fund_id": fund2.id, "split_percentage": Decimal("0.4")})
    await db_session.flush()

    transfer_amount = Decimal("3000.00")
    fees = Decimal("2.50")
    transfer_data = TransactionCreateCashTransfer(
        transaction_type=TransactionType.BANK_TO_BROKERAGE,
        total_amount=transfer_amount,
        fees_commissions=fees,
        transaction_date=datetime.now(timezone.utc)
        # fund_id and target_fund_id should be null for B2B
    )

    expected_bank_deduction = transfer_amount + fees
    expected_fund1_increase = (transfer_amount * Decimal("0.6")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    expected_fund2_increase = (transfer_amount * Decimal("0.4")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    # Ensure rounding doesn't cause mismatch
    if expected_fund1_increase + expected_fund2_increase != transfer_amount:
        expected_fund2_increase = transfer_amount - expected_fund1_increase # Adjust last split

    expected_final_bank = initial_bank_balance - expected_bank_deduction
    expected_final_fund1 = initial_fund1_cash + expected_fund1_increase
    expected_final_fund2 = initial_fund2_cash + expected_fund2_increase

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)

        # Act
        response = await client.post(f"/api/v1/transactions/cash-transfer?club_id={club.id}", json=transfer_data.model_dump(mode='json'))

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert isinstance(response_data, list) # B2B with splits returns a list
        assert len(response_data) == 2
        tx_responses = [TransactionRead(**item) for item in response_data]

        # Find the transaction for each fund
        tx_fund1 = next((tx for tx in tx_responses if tx.fund_id == fund1.id), None)
        tx_fund2 = next((tx for tx in tx_responses if tx.fund_id == fund2.id), None)

        assert tx_fund1 is not None
        assert tx_fund2 is not None
        assert tx_fund1.transaction_type == TransactionType.BANK_TO_BROKERAGE
        assert tx_fund2.transaction_type == TransactionType.BANK_TO_BROKERAGE
        assert tx_fund1.total_amount == expected_fund1_increase
        assert tx_fund2.total_amount == expected_fund2_increase
        # Fee should be applied to one of the transactions (usually the first processed)
        assert (tx_fund1.fees_commissions == fees and tx_fund2.fees_commissions == 0) or \
               (tx_fund1.fees_commissions == 0 and tx_fund2.fees_commissions == fees)

    # Assert Database State
    await db_session.refresh(club)
    await db_session.refresh(fund1)
    await db_session.refresh(fund2)
    assert club.bank_account_balance == expected_final_bank
    assert fund1.brokerage_cash_balance == expected_final_fund1
    assert fund2.brokerage_cash_balance == expected_final_fund2


async def test_record_cash_transfer_brokerage_to_bank_success(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_multiple_funds: tuple[ClubModel, FundModel, FundModel]
):
    """Test successful BROKERAGE_TO_BANK transfer."""
    # Arrange
    club, fund1, _ = setup_multiple_funds # Need fund1 as source
    admin_user = club_admin_user
    initial_bank_balance = club.bank_account_balance
    initial_fund1_cash = fund1.brokerage_cash_balance
    transfer_amount = Decimal("500.00")
    fees = Decimal("1.00")

    transfer_data = TransactionCreateCashTransfer(
        transaction_type=TransactionType.BROKERAGE_TO_BANK,
        fund_id=fund1.id, # Source fund
        total_amount=transfer_amount,
        fees_commissions=fees,
        transaction_date=datetime.now(timezone.utc)
    )
    expected_fund_deduction = transfer_amount + fees
    expected_bank_increase = transfer_amount
    expected_final_fund1 = initial_fund1_cash - expected_fund_deduction
    expected_final_bank = initial_bank_balance + expected_bank_increase

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act
        response = await client.post(f"/api/v1/transactions/cash-transfer?club_id={club.id}", json=transfer_data.model_dump(mode='json'))

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert not isinstance(response_data, list) # B2B returns single tx
        tx_response = TransactionRead(**response_data)
        assert tx_response.fund_id == fund1.id
        assert tx_response.transaction_type == TransactionType.BROKERAGE_TO_BANK
        assert tx_response.total_amount == transfer_amount
        assert tx_response.fees_commissions == fees

    # Assert Database State
    await db_session.refresh(club)
    await db_session.refresh(fund1)
    assert club.bank_account_balance == expected_final_bank
    assert fund1.brokerage_cash_balance == expected_final_fund1


async def test_record_cash_transfer_interfund_success(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_multiple_funds: tuple[ClubModel, FundModel, FundModel]
):
    """Test successful INTERFUND_CASH_TRANSFER."""
    # Arrange
    club, fund1, fund2 = setup_multiple_funds
    admin_user = club_admin_user
    initial_fund1_cash = fund1.brokerage_cash_balance
    initial_fund2_cash = fund2.brokerage_cash_balance
    transfer_amount = Decimal("300.00")
    fees = Decimal("0.50")

    transfer_data = TransactionCreateCashTransfer(
        transaction_type=TransactionType.INTERFUND_CASH_TRANSFER,
        fund_id=fund1.id, # Source fund
        target_fund_id=fund2.id, # Target fund
        total_amount=transfer_amount,
        fees_commissions=fees,
        transaction_date=datetime.now(timezone.utc)
    )
    expected_fund1_deduction = transfer_amount + fees
    expected_fund2_increase = transfer_amount
    expected_final_fund1 = initial_fund1_cash - expected_fund1_deduction
    expected_final_fund2 = initial_fund2_cash + expected_fund2_increase

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act
        response = await client.post(f"/api/v1/transactions/cash-transfer?club_id={club.id}", json=transfer_data.model_dump(mode='json'))

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert not isinstance(response_data, list) # Interfund returns single tx
        tx_response = TransactionRead(**response_data)
        assert tx_response.fund_id == fund1.id # Tx is logged against source fund
        assert tx_response.transaction_type == TransactionType.INTERFUND_CASH_TRANSFER
        assert tx_response.total_amount == transfer_amount
        assert tx_response.fees_commissions == fees

    # Assert Database State
    await db_session.refresh(fund1)
    await db_session.refresh(fund2)
    assert fund1.brokerage_cash_balance == expected_final_fund1
    assert fund2.brokerage_cash_balance == expected_final_fund2


async def test_record_cash_transfer_forbidden_by_member(
    client: AsyncClient,
    club_member_user: UserModel,
    setup_multiple_funds: tuple[ClubModel, FundModel, FundModel]
):
    """Test recording a cash transfer fails when attempted by a non-admin member."""
    # Arrange
    club, fund1, _ = setup_multiple_funds
    member_user = club_member_user
    transfer_data = TransactionCreateCashTransfer(
        transaction_type=TransactionType.BROKERAGE_TO_BANK,
        fund_id=fund1.id,
        total_amount=Decimal("10.00")
    )
    # Mock authentication as member
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)
        # Act
        response = await client.post(f"/api/v1/transactions/cash-transfer?club_id={club.id}", json=transfer_data.model_dump(mode='json'))
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_record_cash_transfer_unauthenticated(
    client: AsyncClient,
    setup_multiple_funds: tuple[ClubModel, FundModel, FundModel]
):
    """Test recording a cash transfer fails without authentication."""
    # Arrange
    club, fund1, _ = setup_multiple_funds
    transfer_data = TransactionCreateCashTransfer(
        transaction_type=TransactionType.BROKERAGE_TO_BANK,
        fund_id=fund1.id,
        total_amount=Decimal("10.00")
    )
    # Act
    response = await client.post(f"/api/v1/transactions/cash-transfer?club_id={club.id}", json=transfer_data.model_dump(mode='json'))
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_record_cash_transfer_insufficient_funds_bank(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_multiple_funds: tuple[ClubModel, FundModel, FundModel]
):
    """Test BANK_TO_BROKERAGE transfer fails with insufficient bank funds."""
    # Arrange
    club, fund1, fund2 = setup_multiple_funds
    admin_user = club_admin_user
    club.bank_account_balance = Decimal("100.00") # Low bank balance
    db_session.add(club)
    await db_session.flush()
    await db_session.refresh(club)
    # Need splits for B2B
    await crud_fund_split.create_fund_split(db_session, fund_split_data={"club_id": club.id, "fund_id": fund1.id, "split_percentage": Decimal("1.0")})
    await db_session.flush()

    transfer_data = TransactionCreateCashTransfer(
        transaction_type=TransactionType.BANK_TO_BROKERAGE,
        total_amount=Decimal("200.00"), # More than available
        fees_commissions=Decimal("1.00")
    )
    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act
        response = await client.post(f"/api/v1/transactions/cash-transfer?club_id={club.id}", json=transfer_data.model_dump(mode='json'))
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient funds in club bank account" in response.json()["detail"]


async def test_record_cash_transfer_insufficient_funds_brokerage(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_multiple_funds: tuple[ClubModel, FundModel, FundModel]
):
    """Test BROKERAGE_TO_BANK transfer fails with insufficient fund brokerage funds."""
    # Arrange
    club, fund1, _ = setup_multiple_funds
    admin_user = club_admin_user
    fund1.brokerage_cash_balance = Decimal("50.00") # Low fund balance
    db_session.add(fund1)
    await db_session.flush()
    await db_session.refresh(fund1)

    transfer_data = TransactionCreateCashTransfer(
        transaction_type=TransactionType.BROKERAGE_TO_BANK,
        fund_id=fund1.id,
        total_amount=Decimal("100.00"), # More than available
        fees_commissions=Decimal("1.00")
    )
    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act
        response = await client.post(f"/api/v1/transactions/cash-transfer?club_id={club.id}", json=transfer_data.model_dump(mode='json'))
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert f"Insufficient funds in source fund '{fund1.name}'" in response.json()["detail"]


async def test_record_cash_transfer_b2b_no_splits(
    client: AsyncClient,
    club_admin_user: UserModel,
    setup_multiple_funds: tuple[ClubModel, FundModel, FundModel]
):
    """Test BANK_TO_BROKERAGE transfer fails if no fund splits are defined."""
    # Arrange
    club, _, _ = setup_multiple_funds # Don't create splits
    admin_user = club_admin_user
    transfer_data = TransactionCreateCashTransfer(
        transaction_type=TransactionType.BANK_TO_BROKERAGE,
        total_amount=Decimal("100.00")
    )
    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act
        response = await client.post(f"/api/v1/transactions/cash-transfer?club_id={club.id}", json=transfer_data.model_dump(mode='json'))
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No fund splits defined" in response.json()["detail"]


async def test_record_cash_transfer_interfund_missing_target(
    client: AsyncClient,
    club_admin_user: UserModel,
    setup_multiple_funds: tuple[ClubModel, FundModel, FundModel]
):
    """Test INTERFUND transfer fails if target_fund_id is missing."""
    # Arrange
    club, fund1, _ = setup_multiple_funds
    admin_user = club_admin_user
    invalid_transfer_data = { # Use dict to bypass Pydantic validation initially
        "transaction_type": TransactionType.INTERFUND_CASH_TRANSFER.value,
        "fund_id": str(fund1.id),
        # "target_fund_id": None, # Missing target
        "total_amount": "50.00",
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act
        response = await client.post(f"/api/v1/transactions/cash-transfer?club_id={club.id}", json=invalid_transfer_data)
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "target_fund_id" in response.json()["detail"][0]["loc"]
        assert "Field 'target_fund_id' is required" in response.json()["detail"][0]["msg"]


async def test_record_cash_transfer_interfund_same_source_target(
    client: AsyncClient,
    club_admin_user: UserModel,
    setup_multiple_funds: tuple[ClubModel, FundModel, FundModel]
):
    """Test INTERFUND transfer fails if source and target funds are the same."""
    # Arrange
    club, fund1, _ = setup_multiple_funds
    admin_user = club_admin_user
    invalid_transfer_data = { # Use dict to bypass Pydantic validation initially
        "transaction_type": TransactionType.INTERFUND_CASH_TRANSFER.value,
        "fund_id": str(fund1.id),
        "target_fund_id": str(fund1.id), # Same source and target
        "total_amount": "50.00",
        "transaction_date": datetime.now(timezone.utc).isoformat()
    }
    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act
        response = await client.post(f"/api/v1/transactions/cash-transfer?club_id={club.id}", json=invalid_transfer_data)
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Source and target fund cannot be the same" in response.json()["detail"][0]["msg"]

# --- API Tests for POST /transactions/option-lifecycle ---

async def test_record_option_exercise_long_call_success(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_option_position: tuple[ClubModel, FundModel, AssetModel, AssetModel, PositionModel]
):
    """Test successfully recording OPTION_EXERCISE for a long call."""
    # Arrange
    club, fund, underlying_asset, option_asset, option_position = setup_option_position
    admin_user = club_admin_user
    initial_fund_cash = fund.brokerage_cash_balance
    initial_option_qty = option_position.quantity # Should be 5.0
    contracts_to_exercise = Decimal("2.0")
    shares_per_contract = Decimal("100")
    strike_price = option_asset.strike_price # Should be 100.00

    lifecycle_data = TransactionCreateOptionLifecycle(
        fund_id=fund.id,
        asset_id=option_asset.id, # The option asset being exercised
        transaction_type=TransactionType.OPTION_EXERCISE,
        quantity=contracts_to_exercise, # Number of contracts exercised
        transaction_date=datetime.now(timezone.utc)
    )

    expected_option_qty_final = initial_option_qty - contracts_to_exercise # 5 - 2 = 3
    expected_stock_qty_change = contracts_to_exercise * shares_per_contract # 2 * 100 = 200
    expected_cash_change = -(expected_stock_qty_change * strike_price) # -(200 * 100) = -20000
    expected_final_fund_cash = initial_fund_cash + expected_cash_change

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)

        # Act
        response = await client.post(f"/api/v1/transactions/option-lifecycle?club_id={club.id}", json=lifecycle_data.model_dump(mode='json'))

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED
        tx_response = TransactionRead(**response.json()) # Primary option transaction
        assert tx_response.fund_id == fund.id
        assert tx_response.asset_id == option_asset.id
        assert tx_response.transaction_type == TransactionType.OPTION_EXERCISE
        assert tx_response.quantity == contracts_to_exercise

    # Assert Database State
    await db_session.refresh(fund)
    await db_session.refresh(option_position)
    assert fund.brokerage_cash_balance == expected_final_fund_cash
    assert option_position.quantity == expected_option_qty_final # Option position reduced

    # Check underlying stock position
    stock_position = await crud_position.get_position_by_fund_and_asset(db=db_session, fund_id=fund.id, asset_id=underlying_asset.id)
    assert stock_position is not None
    assert stock_position.quantity == expected_stock_qty_change # Stock position created/increased
    assert stock_position.average_cost_basis == strike_price # Cost basis is strike


async def test_record_option_expiration_success(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_option_position: tuple[ClubModel, FundModel, AssetModel, AssetModel, PositionModel]
):
    """Test successfully recording OPTION_EXPIRATION for a long position."""
    # Arrange
    club, fund, _, option_asset, option_position = setup_option_position
    admin_user = club_admin_user
    initial_fund_cash = fund.brokerage_cash_balance
    initial_option_qty = option_position.quantity
    contracts_to_expire = initial_option_qty # Expire all contracts held

    lifecycle_data = TransactionCreateOptionLifecycle(
        fund_id=fund.id,
        asset_id=option_asset.id,
        transaction_type=TransactionType.OPTION_EXPIRATION,
        quantity=contracts_to_expire,
        transaction_date=datetime.now(timezone.utc)
    )

    expected_option_qty_final = initial_option_qty - contracts_to_expire # Should be 0

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act
        response = await client.post(f"/api/v1/transactions/option-lifecycle?club_id={club.id}", json=lifecycle_data.model_dump(mode='json'))

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED
        tx_response = TransactionRead(**response.json())
        assert tx_response.transaction_type == TransactionType.OPTION_EXPIRATION
        assert tx_response.quantity == contracts_to_expire

    # Assert Database State
    await db_session.refresh(fund)
    await db_session.refresh(option_position)
    assert fund.brokerage_cash_balance == initial_fund_cash # No cash change on expiration
    assert option_position.quantity == expected_option_qty_final # Option position closed


async def test_record_option_lifecycle_forbidden_by_member(
    client: AsyncClient,
    club_member_user: UserModel,
    setup_option_position: tuple[ClubModel, FundModel, AssetModel, AssetModel, PositionModel]
):
    """Test recording option lifecycle fails when attempted by a non-admin member."""
    # Arrange
    club, fund, _, option_asset, option_position = setup_option_position
    member_user = club_member_user
    lifecycle_data = TransactionCreateOptionLifecycle(
        fund_id=fund.id,
        asset_id=option_asset.id,
        transaction_type=TransactionType.OPTION_EXPIRATION,
        quantity=option_position.quantity
    )
    # Mock authentication as member
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)
        # Act
        response = await client.post(f"/api/v1/transactions/option-lifecycle?club_id={club.id}", json=lifecycle_data.model_dump(mode='json'))
        # Assert
        assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_record_option_lifecycle_unauthenticated(
    client: AsyncClient,
    setup_option_position: tuple[ClubModel, FundModel, AssetModel, AssetModel, PositionModel]
):
    """Test recording option lifecycle fails without authentication."""
    # Arrange
    club, fund, _, option_asset, option_position = setup_option_position
    lifecycle_data = TransactionCreateOptionLifecycle(
        fund_id=fund.id,
        asset_id=option_asset.id,
        transaction_type=TransactionType.OPTION_EXPIRATION,
        quantity=option_position.quantity
    )
    # Act
    response = await client.post(f"/api/v1/transactions/option-lifecycle?club_id={club.id}", json=lifecycle_data.model_dump(mode='json'))
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_record_option_lifecycle_insufficient_quantity(
    client: AsyncClient,
    club_admin_user: UserModel,
    setup_option_position: tuple[ClubModel, FundModel, AssetModel, AssetModel, PositionModel]
):
    """Test recording option exercise fails if quantity exceeds position."""
    # Arrange
    club, fund, _, option_asset, option_position = setup_option_position
    admin_user = club_admin_user
    contracts_to_exercise = option_position.quantity + Decimal("1") # More than held

    lifecycle_data = TransactionCreateOptionLifecycle(
        fund_id=fund.id,
        asset_id=option_asset.id,
        transaction_type=TransactionType.OPTION_EXERCISE,
        quantity=contracts_to_exercise
    )
    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act
        response = await client.post(f"/api/v1/transactions/option-lifecycle?club_id={club.id}", json=lifecycle_data.model_dump(mode='json'))
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "exceeds available" in response.json()["detail"]


async def test_record_option_lifecycle_fund_mismatch(
    client: AsyncClient,
    db_session: AsyncSession,
    club_admin_user: UserModel,
    setup_option_position: tuple[ClubModel, FundModel, AssetModel, AssetModel, PositionModel]
):
    """Test recording option lifecycle fails if fund_id doesn't belong to club_id."""
    # Arrange
    club1, fund1, _, option_asset, option_position = setup_option_position
    admin_user = club_admin_user

    # Create a second club
    other_club_creator = await crud_user.create_user(db_session, user_data={"email": f"other_cl_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|other_cl_{uuid.uuid4()}"})
    await db_session.flush()
    club2 = await crud_club.create_club(db_session, club_data={"name": "Club Four", "creator_id": other_club_creator.id})
    await db_session.flush()

    lifecycle_data = TransactionCreateOptionLifecycle(
        fund_id=fund1.id, # Fund from club1
        asset_id=option_asset.id,
        transaction_type=TransactionType.OPTION_EXPIRATION,
        quantity=option_position.quantity
    )

    # Mock authentication as admin of club1
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        # Act: Try to post to club2's endpoint but with fund_id from club1
        response = await client.post(f"/api/v1/transactions/option-lifecycle?club_id={club2.id}", json=lifecycle_data.model_dump(mode='json'))
        # Assert: Should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert f"Fund {fund1.id} does not belong to club {club2.id}" in response.json()["detail"]

# --- API Tests for GET /transactions ---

async def test_list_transactions_success(
    client: AsyncClient,
    club_member_user: UserModel, # Regular member can list
    setup_multiple_transactions: tuple[ClubModel, FundModel, AssetModel, List[TransactionModel]]
):
    """Test listing all transactions for a club as a member."""
    # Arrange
    club, _, _, expected_transactions = setup_multiple_transactions
    member_user = club_member_user # User making the request

    # Mock authentication as the member user
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)

        # Act
        response = await client.get(f"/api/v1/transactions?club_id={club.id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        assert len(response_data) == len(expected_transactions) # Should only list tx for this club

        retrieved_txs = [TransactionRead(**item) for item in response_data]
        retrieved_ids = {tx.id for tx in retrieved_txs}
        expected_ids = {tx.id for tx in expected_transactions}
        assert retrieved_ids == expected_ids

        # Check default order (desc date)
        assert [tx.id for tx in retrieved_txs] == [tx.id for tx in expected_transactions]


async def test_list_transactions_filter_by_fund(
    client: AsyncClient,
    club_member_user: UserModel,
    setup_multiple_transactions: tuple[ClubModel, FundModel, AssetModel, List[TransactionModel]]
):
    """Test listing transactions filtered by fund_id."""
    # Arrange
    club, fund, _, expected_transactions = setup_multiple_transactions
    member_user = club_member_user

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)
        # Act
        response = await client.get(f"/api/v1/transactions?club_id={club.id}&fund_id={fund.id}")
        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data) == len(expected_transactions) # All created tx were in this fund
        retrieved_ids = {uuid.UUID(item['id']) for item in response_data}
        expected_ids = {tx.id for tx in expected_transactions}
        assert retrieved_ids == expected_ids


async def test_list_transactions_filter_by_asset(
    client: AsyncClient,
    club_member_user: UserModel,
    setup_multiple_transactions: tuple[ClubModel, FundModel, AssetModel, List[TransactionModel]]
):
    """Test listing transactions filtered by asset_id."""
    # Arrange
    club, _, asset, expected_transactions = setup_multiple_transactions
    member_user = club_member_user

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)
        # Act
        response = await client.get(f"/api/v1/transactions?club_id={club.id}&asset_id={asset.id}")
        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        # All created tx involved this asset
        assert len(response_data) == len(expected_transactions)
        retrieved_ids = {uuid.UUID(item['id']) for item in response_data}
        expected_ids = {tx.id for tx in expected_transactions}
        assert retrieved_ids == expected_ids


async def test_list_transactions_pagination(
    client: AsyncClient,
    club_member_user: UserModel,
    setup_multiple_transactions: tuple[ClubModel, FundModel, AssetModel, List[TransactionModel]]
):
    """Test pagination for listing transactions."""
    # Arrange
    club, _, _, expected_transactions = setup_multiple_transactions # 3 transactions created
    member_user = club_member_user
    # Expected order is desc date: tx_sell, tx_div, tx_buy

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)

        # Act: Get first page (limit 2)
        response1 = await client.get(f"/api/v1/transactions?club_id={club.id}&limit=2")
        # Assert Page 1
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert len(data1) == 2
        assert data1[0]['id'] == str(expected_transactions[0].id) # tx_sell
        assert data1[1]['id'] == str(expected_transactions[1].id) # tx_div

        # Act: Get second page (skip 2, limit 2)
        response2 = await client.get(f"/api/v1/transactions?club_id={club.id}&skip=2&limit=2")
        # Assert Page 2
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert len(data2) == 1
        assert data2[0]['id'] == str(expected_transactions[2].id) # tx_buy


async def test_list_transactions_unauthenticated(
    client: AsyncClient,
    setup_multiple_transactions: tuple[ClubModel, FundModel, AssetModel, List[TransactionModel]]
):
    """Test listing transactions fails without authentication."""
    club, _, _, _ = setup_multiple_transactions
    response = await client.get(f"/api/v1/transactions?club_id={club.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_list_transactions_not_member(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel, # User is authenticated
    setup_multiple_transactions: tuple[ClubModel, FundModel, AssetModel, List[TransactionModel]]
):
    """Test listing transactions fails if authenticated user is not a club member."""
    # Arrange
    club, _, _, _ = setup_multiple_transactions # Club exists
    non_member_user = authenticated_user # This user is NOT in the club from the fixture

    # Mock authentication as the non-member user
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: non_member_user)
        # Act
        response = await client.get(f"/api/v1/transactions?club_id={club.id}")
        # Assert: require_club_member dependency should trigger 403
        assert response.status_code == status.HTTP_403_FORBIDDEN


# --- API Tests for GET /transactions/{transaction_id} ---

async def test_get_single_transaction_success(
    client: AsyncClient,
    club_member_user: UserModel,
    setup_multiple_transactions: tuple[ClubModel, FundModel, AssetModel, List[TransactionModel]]
):
    """Test getting a specific transaction as a club member."""
    # Arrange
    club, _, _, transactions = setup_multiple_transactions
    member_user = club_member_user
    target_transaction = transactions[1] # Get the middle one (dividend tx)

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)
        # Act
        response = await client.get(f"/api/v1/transactions/{target_transaction.id}?club_id={club.id}") # Pass club_id

        # Assert
        assert response.status_code == status.HTTP_200_OK
        tx_response = TransactionRead(**response.json())
        assert tx_response.id == target_transaction.id
        assert tx_response.transaction_type == target_transaction.transaction_type
        assert tx_response.total_amount == target_transaction.total_amount


async def test_get_single_transaction_not_found(
    client: AsyncClient,
    club_member_user: UserModel,
    setup_multiple_transactions: tuple[ClubModel, FundModel, AssetModel, List[TransactionModel]]
):
    """Test getting a non-existent transaction ID."""
    # Arrange
    club, _, _, _ = setup_multiple_transactions
    member_user = club_member_user
    non_existent_tx_id = uuid.uuid4()

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)
        # Act
        response = await client.get(f"/api/v1/transactions/{non_existent_tx_id}?club_id={club.id}") # Pass club_id
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_single_transaction_unauthenticated(
    client: AsyncClient,
    setup_multiple_transactions: tuple[ClubModel, FundModel, AssetModel, List[TransactionModel]]
):
    """Test getting a single transaction fails without authentication."""
    # Arrange
    club, _, _, transactions = setup_multiple_transactions
    target_transaction = transactions[0]
    # Act
    response = await client.get(f"/api/v1/transactions/{target_transaction.id}?club_id={club.id}") # Pass club_id
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_single_transaction_not_member(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel, # Authenticated user
    setup_multiple_transactions: tuple[ClubModel, FundModel, AssetModel, List[TransactionModel]]
):
    """Test getting a transaction fails if the user is not a member of the club."""
    # Arrange
    club, _, _, transactions = setup_multiple_transactions # Club where tx exists
    non_member_user = authenticated_user # User not in this club
    target_transaction = transactions[0]

    # Mock authentication as non-member
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: non_member_user)
        # Act
        response = await client.get(f"/api/v1/transactions/{target_transaction.id}?club_id={club.id}") # Pass club_id
        # Assert: require_club_member dependency should trigger 403
        assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_get_single_transaction_wrong_club(
    client: AsyncClient,
    db_session: AsyncSession,
    club_member_user: UserModel, # Member of club1
    setup_multiple_transactions: tuple[ClubModel, FundModel, AssetModel, List[TransactionModel]]
):
    """Test getting a transaction returns 404 if the transaction ID exists but belongs to another club."""
    # Arrange
    club1, _, _, transactions1 = setup_multiple_transactions # User is member of club1
    member_user = club_member_user
    target_transaction = transactions1[0] # A transaction in club1

    # Create club2
    other_user = await crud_user.create_user(db_session, user_data={"email": f"c2_owner_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|c2_owner_{uuid.uuid4()}"})
    await db_session.flush()
    club2 = await crud_club.create_club(db_session, club_data={"name": f"Wrong Club {uuid.uuid4()}", "creator_id": other_user.id})
    await db_session.flush()
    # Add member_user to club2 so they pass the initial require_club_member check for club2
    await crud_membership.create_club_membership(db_session, membership_data={"user_id": member_user.id, "club_id": club2.id, "role": ClubRole.MEMBER})
    await db_session.flush()

    # Mock authentication as the user (who is member of both clubs now)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)
        # Act: Try to get transaction from club1 using club2's endpoint path/query param
        response = await client.get(f"/api/v1/transactions/{target_transaction.id}?club_id={club2.id}") # Use club2's ID

        # Assert: Endpoint logic should return 404 because tx.fund.club_id != club_id from path/query
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert f"Transaction {target_transaction.id} not found in this club" in response.json()["detail"]