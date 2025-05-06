# backend/tests/services/test_asset_service.py

import pytest
import uuid
from decimal import Decimal
from datetime import date, timedelta
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

# Service functions to test
from backend.services import asset_service
# CRUD functions - now used directly instead of mocked
from backend.crud import asset as crud_asset
# Models and Schemas
from backend.models import Asset
from backend.models.enums import AssetType, OptionType, Currency
from backend.schemas import AssetCreateStock, AssetCreateOption

# Import Auth0 mocking fixtures
from backend.tests.auth_fixtures import mock_auth0_token_verification, mock_get_current_active_user, test_user

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio

# --- Tests for get_or_create_stock_asset ---

async def test_get_or_create_stock_asset_new(db_session: AsyncSession):
    """ Test service creates a new stock when it doesn't exist using actual CRUD functions. """
    # Arrange
    symbol = f"NEW_{uuid.uuid4().hex[:6]}"
    name = "New Company"
    asset_in = AssetCreateStock(symbol=symbol, name=name)
    
    # Verify the asset doesn't exist yet
    existing = await crud_asset.get_asset_by_symbol(db=db_session, symbol=symbol.upper())
    assert existing is None
    
    # Act
    result = await asset_service.get_or_create_stock_asset(db=db_session, asset_in=asset_in)
    
    # Assert
    assert result is not None
    assert result.symbol == symbol.upper()
    assert result.name == name
    assert result.asset_type == AssetType.STOCK
    assert result.currency == Currency.USD
    
    # Verify it was actually created in the database
    db_asset = await crud_asset.get_asset_by_symbol(db=db_session, symbol=symbol.upper())
    assert db_asset is not None
    assert db_asset.id == result.id


async def test_get_or_create_stock_asset_existing_stock(db_session: AsyncSession):
    """ Test service returns an existing stock asset using actual CRUD functions. """
    # Arrange - Create a stock asset first
    symbol = f"EXIST_{uuid.uuid4().hex[:6]}"
    name = "Existing Company"
    
    # Create the asset directly with CRUD
    asset_data = {
        "asset_type": AssetType.STOCK,
        "symbol": symbol.upper(),
        "name": name,
        "currency": Currency.USD
    }
    existing_asset = await crud_asset.create_asset(db=db_session, asset_data=asset_data)
    await db_session.flush()
    
    # Create input with different name to verify original is preserved
    asset_in = AssetCreateStock(symbol=symbol, name="Attempt New Name")
    
    # Act
    result = await asset_service.get_or_create_stock_asset(db=db_session, asset_in=asset_in)
    
    # Assert
    assert result is not None
    assert result.id == existing_asset.id
    assert result.symbol == symbol.upper()
    assert result.name == name  # Original name should be preserved
    assert result.asset_type == AssetType.STOCK


async def test_get_or_create_stock_asset_existing_non_stock(db_session: AsyncSession):
    """ Test service raises 409 if a non-stock asset with the same symbol exists using actual CRUD functions. """
    # Arrange - Create a non-stock asset first
    symbol = f"CONFLICT_{uuid.uuid4().hex[:6]}"
    
    # Create an option asset with the symbol
    option_data = {
        "asset_type": AssetType.OPTION,
        "symbol": symbol.upper(),
        "name": "Some Option",
        "currency": Currency.USD,
        "option_type": OptionType.CALL,
        "strike_price": Decimal("100.00"),
        "expiration_date": date.today() + timedelta(days=30)
    }
    await crud_asset.create_asset(db=db_session, asset_data=option_data)
    await db_session.flush()
    
    # Try to create a stock with the same symbol
    asset_in = AssetCreateStock(symbol=symbol, name="New Stock Name")
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await asset_service.get_or_create_stock_asset(db=db_session, asset_in=asset_in)
    
    # Assert exception details
    assert exc_info.value.status_code == 409
    assert f"Symbol '{symbol.upper()}' already exists but is not a stock asset" in exc_info.value.detail


# --- Tests for get_or_create_option_asset ---

async def test_get_or_create_option_new(db_session: AsyncSession):
    """ Test service creates a new option when it doesn't exist using actual CRUD functions. """
    # Arrange - Create underlying stock first
    underlying_symbol = f"UND_{uuid.uuid4().hex[:6]}"
    underlying_data = {
        "asset_type": AssetType.STOCK,
        "symbol": underlying_symbol.upper(),
        "name": "Underlying Stock",
        "currency": Currency.USD
    }
    underlying_asset = await crud_asset.create_asset(db=db_session, asset_data=underlying_data)
    await db_session.flush()
    
    # Option details
    option_type = OptionType.CALL
    strike = Decimal("100.00")
    exp_date = date.today() + timedelta(days=60)
    
    # Create option input
    option_in = AssetCreateOption(
        underlying_symbol=underlying_symbol,
        option_type=option_type,
        strike_price=strike,
        expiration_date=exp_date
    )
    
    # Act
    result = await asset_service.get_or_create_option_asset(db=db_session, asset_in=option_in)
    
    # Assert
    assert result is not None
    assert result.asset_type == AssetType.OPTION
    assert result.underlying_asset_id == underlying_asset.id
    assert result.option_type == option_type
    assert result.strike_price == strike
    assert result.expiration_date == exp_date
    
    # Expected symbol format
    expected_option_symbol = f"{underlying_symbol.upper()}_{exp_date.strftime('%y%m%d')}{option_type.value[0]}{int(strike)}"
    assert result.symbol == expected_option_symbol
    
    # Verify it was created in the database
    db_option = await crud_asset.get_option_by_contract_details(
        db=db_session,
        underlying_asset_id=underlying_asset.id,
        option_type=option_type,
        strike_price=strike,
        expiration_date=exp_date
    )
    assert db_option is not None
    assert db_option.id == result.id


async def test_get_or_create_option_existing(db_session: AsyncSession):
    """ Test service returns an existing option asset using actual CRUD functions. """
    # Arrange - Create underlying stock first
    underlying_symbol = f"UND_EXIST_{uuid.uuid4().hex[:6]}"
    underlying_data = {
        "asset_type": AssetType.STOCK,
        "symbol": underlying_symbol.upper(),
        "name": "Underlying Stock",
        "currency": Currency.USD
    }
    underlying_asset = await crud_asset.create_asset(db=db_session, asset_data=underlying_data)
    await db_session.flush()
    
    # Option details
    option_type = OptionType.PUT
    strike = Decimal("95.00")
    exp_date = date.today() + timedelta(days=90)
    
    # Create the option directly with CRUD
    expected_option_symbol = f"{underlying_symbol.upper()}_{exp_date.strftime('%y%m%d')}{option_type.value[0]}{int(strike)}"
    expected_option_name = f"{underlying_symbol.upper()} {exp_date.strftime('%b %d %Y')} ${strike:.2f} {option_type.value}"
    
    option_data = {
        "asset_type": AssetType.OPTION,
        "symbol": expected_option_symbol,
        "name": expected_option_name,
        "currency": Currency.USD,
        "underlying_asset_id": underlying_asset.id,
        "option_type": option_type,
        "strike_price": strike,
        "expiration_date": exp_date
    }
    existing_option = await crud_asset.create_asset(db=db_session, asset_data=option_data)
    await db_session.flush()
    
    # Create option input
    option_in = AssetCreateOption(
        underlying_symbol=underlying_symbol,
        option_type=option_type,
        strike_price=strike,
        expiration_date=exp_date
    )
    
    # Act
    result = await asset_service.get_or_create_option_asset(db=db_session, asset_in=option_in)
    
    # Assert
    assert result is not None
    assert result.id == existing_option.id
    assert result.symbol == expected_option_symbol
    assert result.underlying_asset_id == underlying_asset.id


async def test_get_or_create_option_asset_underlying_not_stock(db_session: AsyncSession):
    """ Test creating an option fails if underlying symbol exists but is not STOCK using actual CRUD functions. """
    # Arrange - Create a non-stock asset with the underlying symbol
    underlying_symbol = f"UND_NOT_STOCK_{uuid.uuid4().hex[:6]}"
    
    # Create an option asset with the symbol that would be used as underlying
    non_stock_data = {
        "asset_type": AssetType.OPTION,  # Not a stock
        "symbol": underlying_symbol.upper(),
        "name": "Not a Stock",
        "currency": Currency.USD,
        "option_type": OptionType.CALL,
        "strike_price": Decimal("50.00"),
        "expiration_date": date.today() + timedelta(days=30)
    }
    await crud_asset.create_asset(db=db_session, asset_data=non_stock_data)
    await db_session.flush()
    
    # Create option input using the non-stock as underlying
    option_in = AssetCreateOption(
        underlying_symbol=underlying_symbol,
        option_type=OptionType.CALL,
        strike_price=Decimal("100.00"),
        expiration_date=date.today() + timedelta(days=30)
    )
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await asset_service.get_or_create_option_asset(db=db_session, asset_in=option_in)
    
    assert exc_info.value.status_code == 409
    assert f"Symbol '{underlying_symbol.upper()}' already exists but is not a stock asset" in exc_info.value.detail


# --- Tests for get_asset_by_id ---

async def test_get_asset_by_id_found(db_session: AsyncSession):
    """ Test retrieving an asset by ID successfully using actual CRUD functions. """
    # Arrange - Create an asset first
    asset_data = {
        "asset_type": AssetType.STOCK,
        "symbol": f"FOUND_{uuid.uuid4().hex[:6]}",
        "name": "Found Asset",
        "currency": Currency.USD
    }
    asset = await crud_asset.create_asset(db=db_session, asset_data=asset_data)
    await db_session.flush()
    
    # Act
    result = await asset_service.get_asset_by_id(db=db_session, asset_id=asset.id)
    
    # Assert
    assert result is not None
    assert result.id == asset.id
    assert result.symbol == asset_data["symbol"]
    assert result.name == asset_data["name"]


async def test_get_asset_by_id_not_found(db_session: AsyncSession):
    """ Test retrieving an asset by ID raises 404 when not found using actual CRUD functions. """
    # Arrange
    non_existent_id = uuid.uuid4()
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await asset_service.get_asset_by_id(db=db_session, asset_id=non_existent_id)
    
    assert exc_info.value.status_code == 404
    assert f"Asset with id {non_existent_id} not found" in exc_info.value.detail


# --- Tests for list_assets ---

async def test_list_assets_success(db_session: AsyncSession):
    """ Test listing assets successfully using actual CRUD functions. """
    # Arrange - Create multiple assets
    assets_to_create = [
        {
            "asset_type": AssetType.STOCK,
            "symbol": f"LIST1_{uuid.uuid4().hex[:6]}",
            "name": "List Asset 1",
            "currency": Currency.USD
        },
        {
            "asset_type": AssetType.STOCK,
            "symbol": f"LIST2_{uuid.uuid4().hex[:6]}",
            "name": "List Asset 2",
            "currency": Currency.USD
        }
    ]
    
    for asset_data in assets_to_create:
        await crud_asset.create_asset(db=db_session, asset_data=asset_data)
    await db_session.flush()
    
    # Act
    result = await asset_service.list_assets(db=db_session, skip=0, limit=10)
    
    # Assert
    assert len(result) >= 2  # At least our 2 assets should be there
    # Check that our created assets are in the results
    created_symbols = [asset_data["symbol"] for asset_data in assets_to_create]
    result_symbols = [asset.symbol for asset in result]
    
    for symbol in created_symbols:
        assert symbol in result_symbols
