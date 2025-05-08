# backend/tests/api/test_assets_api.py

import pytest
import pytest_asyncio
import uuid
from decimal import Decimal
from datetime import date, timedelta
from typing import AsyncGenerator
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

# Import the FastAPI app instance
from backend.main import app

# Import schemas and models
from backend.schemas import AssetCreateStock, AssetCreateOption, AssetRead
from backend.models import User as UserModel, Asset as AssetModel
from backend.models.enums import AssetType, OptionType, Currency

# Import CRUD functions for verification/setup
from backend.crud import asset as crud_asset
from backend.crud import user as crud_user

# Import fixtures
from backend.tests.auth_fixtures import authenticated_user, test_user
from backend.tests.conftest import db_session

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio


# --- Test Fixture for API Client ---
@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an asynchronous test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

# --- API Tests for POST /assets/stock ---

async def test_get_or_create_stock_asset_success_new(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel # Mocks auth
):
    """Test creating a new stock asset via POST /assets/stock."""
    # Arrange
    symbol = f"NEWSTK_{uuid.uuid4().hex[:4]}"
    name = "New Stock Company"
    stock_data = AssetCreateStock(symbol=symbol, name=name)

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: authenticated_user)

        # Act
        response = await client.post("/api/v1/assets/stock", json=stock_data.model_dump())

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        asset_response = AssetRead(**response_data)
        assert asset_response.symbol == symbol.upper()
        assert asset_response.name == name
        assert asset_response.asset_type == AssetType.STOCK
        assert asset_response.id is not None

    # Assert Database State
    db_asset = await crud_asset.get_asset_by_symbol(db=db_session, symbol=symbol)
    assert db_asset is not None
    assert db_asset.id == asset_response.id
    assert db_asset.asset_type == AssetType.STOCK


async def test_get_or_create_stock_asset_success_existing(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel
):
    """Test retrieving an existing stock asset via POST /assets/stock."""
    # Arrange: Create the asset first
    symbol = f"EXISTSTK_{uuid.uuid4().hex[:4]}"
    name = "Existing Stock Company"
    existing_asset = await crud_asset.create_asset(
        db_session,
        asset_data={"asset_type": AssetType.STOCK, "symbol": symbol.upper(), "name": name, "currency": Currency.USD}
    )
    await db_session.flush()

    stock_data = AssetCreateStock(symbol=symbol, name="Attempt New Name") # Try with different name

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: authenticated_user)

        # Act
        response = await client.post("/api/v1/assets/stock", json=stock_data.model_dump())

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED # Service returns 201 even if exists
        response_data = response.json()
        asset_response = AssetRead(**response_data)
        assert asset_response.id == existing_asset.id
        assert asset_response.symbol == symbol.upper()
        assert asset_response.name == name # Should return original name
        assert asset_response.asset_type == AssetType.STOCK


async def test_get_or_create_stock_asset_conflict(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel
):
    """Test POST /assets/stock fails if symbol exists but is not a stock."""
    # Arrange: Create an option with the target symbol
    symbol = f"CONFLICT_{uuid.uuid4().hex[:4]}"
    await crud_asset.create_asset(
        db_session,
        asset_data={
            "asset_type": AssetType.OPTION, # Not a stock
            "symbol": symbol.upper(),
            "name": "Conflicting Option",
            "currency": Currency.USD,
            "option_type": OptionType.CALL,
            "strike_price": Decimal("10"),
            "expiration_date": date.today() + timedelta(days=10)
            # underlying_asset_id would be needed for a real option, but not for this conflict test
        }
    )
    await db_session.flush()

    stock_data = AssetCreateStock(symbol=symbol, name="Conflicting Stock")

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: authenticated_user)

        # Act
        response = await client.post("/api/v1/assets/stock", json=stock_data.model_dump())

        # Assert API Response (Service should raise 409)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists but is not a stock asset" in response.json()["detail"]


async def test_get_or_create_stock_asset_unauthenticated(
    client: AsyncClient
):
    """Test POST /assets/stock fails without authentication."""
    # Arrange
    stock_data = AssetCreateStock(symbol="UNAUTH", name="Unauthorized Stock")
    # Act
    response = await client.post("/api/v1/assets/stock", json=stock_data.model_dump())
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- API Tests for POST /assets/option ---

async def test_get_or_create_option_asset_success_new(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel
):
    """Test creating a new option asset via POST /assets/option."""
    # Arrange: Create underlying stock first
    underlying_symbol = f"UND_{uuid.uuid4().hex[:4]}"
    underlying_name = "Underlying Corp"
    underlying_asset = await crud_asset.create_asset(
        db_session,
        asset_data={"asset_type": AssetType.STOCK, "symbol": underlying_symbol.upper(), "name": underlying_name, "currency": Currency.USD}
    )
    await db_session.flush()

    option_data = AssetCreateOption(
        underlying_symbol=underlying_symbol,
        option_type=OptionType.PUT,
        strike_price=Decimal("50.00"),
        expiration_date=date.today() + timedelta(days=90)
    )

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: authenticated_user)

        # Act
        response = await client.post("/api/v1/assets/option", json=option_data.model_dump(mode='json')) # Use mode='json' for Decimal/Date

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        asset_response = AssetRead(**response_data)
        assert asset_response.asset_type == AssetType.OPTION
        assert asset_response.underlying_asset_id == underlying_asset.id
        assert asset_response.option_type == OptionType.PUT
        assert asset_response.strike_price == option_data.strike_price
        assert asset_response.expiration_date == option_data.expiration_date
        # Check underlying asset details are nested correctly
        assert asset_response.underlying_asset is not None
        assert asset_response.underlying_asset.id == underlying_asset.id
        assert asset_response.underlying_asset.symbol == underlying_symbol.upper()

    # Assert Database State
    db_asset = await crud_asset.get_asset(db=db_session, asset_id=asset_response.id)
    assert db_asset is not None
    assert db_asset.asset_type == AssetType.OPTION
    assert db_asset.underlying_asset_id == underlying_asset.id


async def test_get_or_create_option_asset_success_existing(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel
):
    """Test retrieving an existing option asset via POST /assets/option."""
    # Arrange: Create underlying and option first
    underlying_symbol = f"UNDEX_{uuid.uuid4().hex[:4]}"
    underlying_asset = await crud_asset.create_asset(
        db_session,
        asset_data={"asset_type": AssetType.STOCK, "symbol": underlying_symbol.upper(), "name": "Existing Underlying", "currency": Currency.USD}
    )
    await db_session.flush()

    strike = Decimal("120.00")
    exp_date = date.today() + timedelta(days=180)
    opt_type = OptionType.CALL
    existing_option = await crud_asset.create_asset(
        db_session,
        asset_data={
            "asset_type": AssetType.OPTION,
            "symbol": f"{underlying_symbol.upper()}_{exp_date.strftime('%y%m%d')}C{int(strike)}",
            "name": f"{underlying_symbol.upper()} Option",
            "currency": Currency.USD,
            "underlying_asset_id": underlying_asset.id,
            "option_type": opt_type,
            "strike_price": strike,
            "expiration_date": exp_date
        }
    )
    await db_session.flush()

    option_data = AssetCreateOption(
        underlying_symbol=underlying_symbol,
        option_type=opt_type,
        strike_price=strike,
        expiration_date=exp_date
    )

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: authenticated_user)

        # Act
        response = await client.post("/api/v1/assets/option", json=option_data.model_dump(mode='json'))

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED # Service returns 201 even if exists
        response_data = response.json()
        asset_response = AssetRead(**response_data)
        assert asset_response.id == existing_option.id
        assert asset_response.asset_type == AssetType.OPTION
        assert asset_response.underlying_asset_id == underlying_asset.id


async def test_get_or_create_option_asset_underlying_not_found(
    client: AsyncClient,
    authenticated_user: UserModel
):
    """Test POST /assets/option fails if underlying symbol does not exist (will try to create it)."""
    # Arrange
    underlying_symbol = f"NOSUCH_{uuid.uuid4().hex[:4]}"
    option_data = AssetCreateOption(
        underlying_symbol=underlying_symbol,
        option_type=OptionType.CALL,
        strike_price=Decimal("100"),
        expiration_date=date.today() + timedelta(days=30)
    )

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: authenticated_user)

        # Act: The service will first try to get/create the underlying stock
        response = await client.post("/api/v1/assets/option", json=option_data.model_dump(mode='json'))

        # Assert: Should succeed by creating both underlying and option
        assert response.status_code == status.HTTP_201_CREATED
        asset_response = AssetRead(**response.json())
        assert asset_response.asset_type == AssetType.OPTION
        assert asset_response.underlying_asset is not None
        assert asset_response.underlying_asset.symbol == underlying_symbol.upper()


async def test_get_or_create_option_asset_unauthenticated(
    client: AsyncClient
):
    """Test POST /assets/option fails without authentication."""
    # Arrange
    option_data = AssetCreateOption(
        underlying_symbol="ANY",
        option_type=OptionType.CALL,
        strike_price=Decimal("100"),
        expiration_date=date.today() + timedelta(days=30)
    )
    # Act
    response = await client.post("/api/v1/assets/option", json=option_data.model_dump(mode='json'))
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- API Tests for GET /assets ---

async def test_list_assets_success(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel
):
    """Test GET /assets successfully lists assets."""
    # Arrange: Create some assets
    asset1 = await crud_asset.create_asset(db_session, asset_data={"asset_type": AssetType.STOCK, "symbol": "LIST1", "currency": Currency.USD})
    asset2 = await crud_asset.create_asset(db_session, asset_data={"asset_type": AssetType.STOCK, "symbol": "LIST2", "currency": Currency.USD})
    await db_session.flush()
    expected_ids = {asset1.id, asset2.id}

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: authenticated_user)

        # Act
        response = await client.get("/api/v1/assets")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        # Check if the created assets are in the response (might be others from previous tests)
        retrieved_ids = {uuid.UUID(item['id']) for item in response_data}
        assert expected_ids.issubset(retrieved_ids)


async def test_list_assets_pagination(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel
):
    """Test pagination for GET /assets."""
    # Arrange: Create assets (ensure distinct symbols for reliable ordering)
    asset_a = await crud_asset.create_asset(db_session, asset_data={"asset_type": AssetType.STOCK, "symbol": "PAGE_A", "currency": Currency.USD})
    asset_b = await crud_asset.create_asset(db_session, asset_data={"asset_type": AssetType.STOCK, "symbol": "PAGE_B", "currency": Currency.USD})
    asset_c = await crud_asset.create_asset(db_session, asset_data={"asset_type": AssetType.STOCK, "symbol": "PAGE_C", "currency": Currency.USD})
    await db_session.flush()

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: authenticated_user)

        # Act: Get page 1 (limit 2) - Order is by symbol
        response1 = await client.get("/api/v1/assets?limit=2")
        # Assert Page 1
        assert response1.status_code == status.HTTP_200_OK
        data1 = response1.json()
        assert len(data1) == 2
        assert data1[0]['symbol'] == "PAGE_A"
        assert data1[1]['symbol'] == "PAGE_B"

        # Act: Get page 2 (skip 2, limit 2)
        response2 = await client.get("/api/v1/assets?skip=2&limit=2")
        # Assert Page 2
        assert response2.status_code == status.HTTP_200_OK
        data2 = response2.json()
        assert len(data2) == 1
        assert data2[0]['symbol'] == "PAGE_C"


async def test_list_assets_unauthenticated(
    client: AsyncClient
):
    """Test GET /assets fails without authentication."""
    # Act
    response = await client.get("/api/v1/assets")
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# --- API Tests for GET /assets/{asset_id} ---

async def test_get_asset_details_success(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel
):
    """Test GET /assets/{asset_id} successfully retrieves details."""
    # Arrange: Create an asset
    asset = await crud_asset.create_asset(db_session, asset_data={"asset_type": AssetType.STOCK, "symbol": "DETAIL", "name": "Detail Asset", "currency": Currency.USD})
    await db_session.flush()

    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: authenticated_user)

        # Act
        response = await client.get(f"/api/v1/assets/{asset.id}")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        asset_response = AssetRead(**response.json())
        assert asset_response.id == asset.id
        assert asset_response.symbol == "DETAIL"
        assert asset_response.name == "Detail Asset"


async def test_get_asset_details_not_found(
    client: AsyncClient,
    authenticated_user: UserModel
):
    """Test GET /assets/{asset_id} returns 404 for non-existent ID."""
    # Arrange
    non_existent_id = uuid.uuid4()
    # Mock authentication
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: authenticated_user)
        # Act
        response = await client.get(f"/api/v1/assets/{non_existent_id}")
        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_asset_details_unauthenticated(
    client: AsyncClient,
    db_session: AsyncSession
):
    """Test GET /assets/{asset_id} fails without authentication."""
    # Arrange: Create an asset
    asset = await crud_asset.create_asset(db_session, asset_data={"asset_type": AssetType.STOCK, "symbol": "AUTH_TEST", "currency": Currency.USD})
    await db_session.flush()
    # Act
    response = await client.get(f"/api/v1/assets/{asset.id}")
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

