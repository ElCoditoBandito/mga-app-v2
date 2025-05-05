# backend/tests/services/test_asset_service.py

import pytest
import uuid
from decimal import Decimal
from datetime import date, timedelta
from typing import Sequence # Added Sequence
from unittest.mock import patch, AsyncMock, call, MagicMock # Import mocking utilities

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError # Import for simulating DB errors
from fastapi import HTTPException

# Service functions to test
from backend.services import asset_service
# CRUD functions - Will be mocked
# Models and Schemas - For type hints and data structures
from backend.models import Asset
from backend.models.enums import AssetType, OptionType, Currency
from backend.schemas import AssetCreateStock, AssetCreateOption

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio

# --- Constants for Mocks ---
MOCK_STOCK_UUID = uuid.uuid4()
MOCK_OPTION_UUID = uuid.uuid4()
MOCK_UNDERLYING_UUID = uuid.uuid4()

# --- Service Tests with Mocking ---

# --- Tests for get_or_create_stock_asset ---

@patch('backend.services.asset_service.crud_asset.get_asset_by_symbol', new_callable=AsyncMock)
@patch('backend.services.asset_service.crud_asset.create_asset', new_callable=AsyncMock)
async def test_get_or_create_stock_asset_new(mock_create: AsyncMock, mock_get: AsyncMock, db_session: AsyncSession):
    """ Test service creates a new stock when it doesn't exist. """
    # Arrange
    symbol = f"NEW_{uuid.uuid4().hex[:6]}"
    name = "New Company"
    asset_in = AssetCreateStock(symbol=symbol, name=name)
    mock_get.return_value = None # Simulate asset not found
    # Define the expected return object from the mocked create_asset
    expected_asset = Asset(id=MOCK_STOCK_UUID, symbol=symbol.upper(), name=name, asset_type=AssetType.STOCK, currency=Currency.USD)
    mock_create.return_value = expected_asset
    # Define expected data passed to create_asset
    expected_crud_data = {
        "asset_type": AssetType.STOCK, "symbol": symbol.upper(), "name": name,
        "currency": Currency.USD, "option_type": None, "strike_price": None,
        "expiration_date": None, "underlying_asset_id": None,
    }

    # Act
    result = await asset_service.get_or_create_stock_asset(db=db_session, asset_in=asset_in)

    # Assert
    mock_get.assert_called_once_with(db=db_session, symbol=symbol.upper())
    mock_create.assert_called_once_with(db=db_session, asset_data=expected_crud_data)
    assert result == expected_asset

@patch('backend.services.asset_service.crud_asset.get_asset_by_symbol', new_callable=AsyncMock)
@patch('backend.services.asset_service.crud_asset.create_asset', new_callable=AsyncMock)
async def test_get_or_create_stock_asset_existing_stock(mock_create: AsyncMock, mock_get: AsyncMock, db_session: AsyncSession):
    """ Test service returns an existing stock asset. """
    # Arrange
    symbol = f"EXIST_{uuid.uuid4().hex[:6]}"
    name = "Existing Company"
    asset_in = AssetCreateStock(symbol=symbol, name="Attempt New Name") # Input name differs
    # Simulate finding an existing STOCK asset
    existing_asset = Asset(id=MOCK_STOCK_UUID, symbol=symbol.upper(), name=name, asset_type=AssetType.STOCK, currency=Currency.USD)
    mock_get.return_value = existing_asset

    # Act
    result = await asset_service.get_or_create_stock_asset(db=db_session, asset_in=asset_in)

    # Assert
    mock_get.assert_called_once_with(db=db_session, symbol=symbol.upper())
    mock_create.assert_not_called() # Should not create
    assert result == existing_asset # Should return the existing object

# FIX: Updated test to expect HTTPException 409
@patch('backend.services.asset_service.crud_asset.get_asset_by_symbol', new_callable=AsyncMock)
@patch('backend.services.asset_service.crud_asset.create_asset', new_callable=AsyncMock)
async def test_get_or_create_stock_asset_existing_non_stock(mock_create: AsyncMock, mock_get: AsyncMock, db_session: AsyncSession):
    """ Test service raises 409 if a non-stock asset with the same symbol exists. """
    # Arrange
    symbol = f"CONFLICT_{uuid.uuid4().hex[:6]}"
    name = "New Stock Name"
    asset_in = AssetCreateStock(symbol=symbol, name=name)
    # Simulate finding an existing OPTION asset with the same symbol
    existing_non_stock_asset = Asset(id=uuid.uuid4(), symbol=symbol.upper(), name="Some Option", asset_type=AssetType.OPTION, currency=Currency.USD)
    mock_get.return_value = existing_non_stock_asset

    # Act & Assert: Expect HTTPException 409
    with pytest.raises(HTTPException) as exc_info:
        await asset_service.get_or_create_stock_asset(db=db_session, asset_in=asset_in)

    # Assert exception details
    assert exc_info.value.status_code == 409
    assert f"Symbol '{symbol.upper()}' already exists but is not a stock asset" in exc_info.value.detail

    # Assert mocks
    mock_get.assert_called_once_with(db=db_session, symbol=symbol.upper())
    mock_create.assert_not_called() # Create should not be called

@patch('backend.services.asset_service.crud_asset.get_asset_by_symbol', new_callable=AsyncMock)
@patch('backend.services.asset_service.crud_asset.create_asset', new_callable=AsyncMock)
async def test_get_or_create_stock_integrity_error_on_create(mock_create: AsyncMock, mock_get: AsyncMock, db_session: AsyncSession):
    """ Test service handles IntegrityError during stock creation (e.g., concurrent creation). """
    # Arrange
    symbol = f"INTEGRITY_{uuid.uuid4().hex[:6]}"
    asset_in = AssetCreateStock(symbol=symbol, name="Integrity Test")
    mock_get.return_value = None # Asset initially not found
    # Simulate create_asset raising IntegrityError
    mock_create.side_effect = IntegrityError("Mock Integrity Error", params={}, orig=Exception())
    # Simulate that refetching *after* the error finds the concurrently created asset
    # We achieve this by changing the behavior of mock_get on subsequent calls
    final_existing_asset = Asset(id=MOCK_STOCK_UUID, symbol=symbol.upper(), name="Concurrently Created", asset_type=AssetType.STOCK, currency=Currency.USD)
    mock_get.side_effect = [None, final_existing_asset] # First call returns None, second returns the asset

    # Act & Assert Exception is handled and existing asset returned
    result = await asset_service.get_or_create_stock_asset(db=db_session, asset_in=asset_in)

    # Assert
    assert mock_get.call_count == 2
    assert mock_get.call_args_list[0] == call(db=db_session, symbol=symbol.upper())
    assert mock_get.call_args_list[1] == call(db=db_session, symbol=symbol.upper())
    mock_create.assert_called_once() # Create was attempted once
    assert result == final_existing_asset # Returns the refetched asset


@patch('backend.services.asset_service.crud_asset.get_asset_by_symbol', new_callable=AsyncMock)
@patch('backend.services.asset_service.crud_asset.create_asset', new_callable=AsyncMock)
async def test_get_or_create_stock_integrity_error_refetch_fails(mock_create: AsyncMock, mock_get: AsyncMock, db_session: AsyncSession):
    """ Test service raises 409 if IntegrityError occurs and refetch doesn't find stock. """
    # Arrange
    symbol = f"INTEGRITY_FAIL_{uuid.uuid4().hex[:6]}"
    asset_in = AssetCreateStock(symbol=symbol, name="Integrity Fail Test")
    mock_get.return_value = None # Asset initially not found
    mock_create.side_effect = IntegrityError("Mock Integrity Error", params={}, orig=Exception())
    # Simulate refetch *still* finding nothing (or finding a non-stock asset)
    mock_get.side_effect = [None, None] # Both calls return None

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await asset_service.get_or_create_stock_asset(db=db_session, asset_in=asset_in)

    assert exc_info.value.status_code == 409
    assert f"Failed to create stock asset for symbol '{symbol.upper()}'" in exc_info.value.detail
    assert mock_get.call_count == 2
    mock_create.assert_called_once()

# --- Tests for get_or_create_option_asset ---

# Use nested patches for mocking functions called within the service
@patch('backend.services.asset_service.crud_asset.create_asset', new_callable=AsyncMock)
@patch('backend.services.asset_service.crud_asset.get_option_by_contract_details', new_callable=AsyncMock)
@patch('backend.services.asset_service.get_or_create_stock_asset', new_callable=AsyncMock) # Mock the nested service call
async def test_get_or_create_option_new(mock_get_create_stock: AsyncMock, mock_get_option: AsyncMock, mock_create_option: AsyncMock, db_session: AsyncSession):
    """ Test service creates a new option when it doesn't exist. """
    # Arrange
    underlying_symbol = f"UND_{uuid.uuid4().hex[:6]}"
    option_type = OptionType.CALL
    strike = Decimal("100.00")
    exp_date = date.today() + timedelta(days=60)
    option_in = AssetCreateOption(underlying_symbol=underlying_symbol, option_type=option_type, strike_price=strike, expiration_date=exp_date)

    # Mock the underlying stock asset returned by the nested service call
    mock_underlying_asset = Asset(id=MOCK_UNDERLYING_UUID, symbol=underlying_symbol.upper(), name="Underlying", asset_type=AssetType.STOCK, currency=Currency.USD)
    mock_get_create_stock.return_value = mock_underlying_asset

    # Mock finding no existing option
    mock_get_option.return_value = None

    # Mock the successful creation of the option
    expected_option_symbol = f"{underlying_symbol.upper()}_{exp_date.strftime('%y%m%d')}{option_type.value[0]}{int(strike)}"
    expected_option_name = f"{underlying_symbol.upper()} {exp_date.strftime('%b %d %Y')} ${strike:.2f} {option_type.value}"
    expected_option = Asset(id=MOCK_OPTION_UUID, symbol=expected_option_symbol, name=expected_option_name, asset_type=AssetType.OPTION, currency=Currency.USD, underlying_asset_id=MOCK_UNDERLYING_UUID, option_type=option_type, strike_price=strike, expiration_date=exp_date)
    mock_create_option.return_value = expected_option

    # Act
    result = await asset_service.get_or_create_option_asset(db=db_session, asset_in=option_in)

    # Assert
    mock_get_create_stock.assert_called_once() # Check underlying was handled
    mock_get_option.assert_called_once_with(db=db_session, underlying_asset_id=MOCK_UNDERLYING_UUID, option_type=option_type, strike_price=strike, expiration_date=exp_date)
    mock_create_option.assert_called_once() # Option was created
    # Check specific args passed to create_option mock
    create_args, create_kwargs = mock_create_option.call_args
    assert create_kwargs['asset_data']['symbol'] == expected_option_symbol
    assert create_kwargs['asset_data']['underlying_asset_id'] == MOCK_UNDERLYING_UUID
    # ... check other fields if needed
    assert result == expected_option

@patch('backend.services.asset_service.crud_asset.create_asset', new_callable=AsyncMock)
@patch('backend.services.asset_service.crud_asset.get_option_by_contract_details', new_callable=AsyncMock)
@patch('backend.services.asset_service.get_or_create_stock_asset', new_callable=AsyncMock)
async def test_get_or_create_option_existing(mock_get_create_stock: AsyncMock, mock_get_option: AsyncMock, mock_create_option: AsyncMock, db_session: AsyncSession):
    """ Test service returns an existing option asset. """
    # Arrange
    underlying_symbol = f"UND_EXIST_{uuid.uuid4().hex[:6]}"
    option_type = OptionType.PUT
    strike = Decimal("95.00")
    exp_date = date.today() + timedelta(days=90)
    option_in = AssetCreateOption(underlying_symbol=underlying_symbol, option_type=option_type, strike_price=strike, expiration_date=exp_date)

    mock_underlying_asset = Asset(id=MOCK_UNDERLYING_UUID, symbol=underlying_symbol.upper(), name="Underlying", asset_type=AssetType.STOCK, currency=Currency.USD)
    mock_get_create_stock.return_value = mock_underlying_asset

    # Mock finding an existing option
    existing_option = Asset(id=MOCK_OPTION_UUID, symbol="EXIST_OPT", name="Existing", asset_type=AssetType.OPTION, currency=Currency.USD, underlying_asset_id=MOCK_UNDERLYING_UUID, option_type=option_type, strike_price=strike, expiration_date=exp_date)
    mock_get_option.return_value = existing_option

    # Act
    result = await asset_service.get_or_create_option_asset(db=db_session, asset_in=option_in)

    # Assert
    mock_get_create_stock.assert_called_once()
    mock_get_option.assert_called_once_with(db=db_session, underlying_asset_id=MOCK_UNDERLYING_UUID, option_type=option_type, strike_price=strike, expiration_date=exp_date)
    mock_create_option.assert_not_called() # Option was not created
    assert result == existing_option

@patch('backend.services.asset_service.get_or_create_stock_asset', new_callable=AsyncMock) # Only need to mock the nested service call
async def test_get_or_create_option_asset_underlying_not_stock(mock_get_create_stock: AsyncMock, db_session: AsyncSession):
    """ Test creating an option fails if underlying symbol exists but is not STOCK (raises 409). """
    # Arrange
    underlying_symbol = f"UND_NOT_STOCK_{uuid.uuid4().hex[:6]}"
    option_in = AssetCreateOption(
        underlying_symbol=underlying_symbol, option_type=OptionType.CALL,
        strike_price=Decimal("100"), expiration_date=date.today() + timedelta(days=30)
    )
    # Mock the nested service call to raise the expected 409 error
    mock_get_create_stock.side_effect = HTTPException(
        status_code=409,
        detail=f"Symbol '{underlying_symbol.upper()}' already exists but is not a stock asset."
    )

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await asset_service.get_or_create_option_asset(db=db_session, asset_in=option_in)

    assert exc_info.value.status_code == 409
    assert f"Symbol '{underlying_symbol.upper()}' already exists but is not a stock asset" in exc_info.value.detail
    mock_get_create_stock.assert_called_once() # Verify the nested call was made


# --- Tests for get_asset_by_id ---

@patch('backend.services.asset_service.crud_asset.get_asset', new_callable=AsyncMock)
async def test_get_asset_by_id_found(mock_get: AsyncMock, db_session: AsyncSession):
    """ Test retrieving an asset by ID successfully. """
    # Arrange
    asset_id = uuid.uuid4()
    expected_asset = Asset(id=asset_id, symbol="FOUND", name="Found Asset", asset_type=AssetType.STOCK, currency=Currency.USD)
    mock_get.return_value = expected_asset

    # Act
    result = await asset_service.get_asset_by_id(db=db_session, asset_id=asset_id)

    # Assert
    mock_get.assert_called_once_with(db=db_session, asset_id=asset_id)
    assert result == expected_asset

@patch('backend.services.asset_service.crud_asset.get_asset', new_callable=AsyncMock)
async def test_get_asset_by_id_not_found(mock_get: AsyncMock, db_session: AsyncSession):
    """ Test retrieving an asset by ID raises 404 when not found. """
    # Arrange
    asset_id = uuid.uuid4()
    mock_get.return_value = None # Simulate not found

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await asset_service.get_asset_by_id(db=db_session, asset_id=asset_id)

    assert exc_info.value.status_code == 404
    assert f"Asset with id {asset_id} not found" in exc_info.value.detail
    mock_get.assert_called_once_with(db=db_session, asset_id=asset_id)

# --- Tests for list_assets ---

@patch('backend.services.asset_service.crud_asset.get_multi_assets', new_callable=AsyncMock)
async def test_list_assets_success(mock_list: AsyncMock, db_session: AsyncSession):
    """ Test listing assets successfully. """
    # Arrange
    skip, limit = 0, 100
    expected_assets = [
        Asset(id=uuid.uuid4(), symbol="ASSET1", asset_type=AssetType.STOCK, currency=Currency.USD),
        Asset(id=uuid.uuid4(), symbol="ASSET2", asset_type=AssetType.STOCK, currency=Currency.USD),
    ]
    mock_list.return_value = expected_assets

    # Act
    result = await asset_service.list_assets(db=db_session, skip=skip, limit=limit)

    # Assert
    mock_list.assert_called_once_with(db=db_session, skip=skip, limit=limit)
    assert result == expected_assets

@patch('backend.services.asset_service.crud_asset.get_multi_assets', new_callable=AsyncMock)
async def test_list_assets_empty(mock_list: AsyncMock, db_session: AsyncSession):
    """ Test listing assets when the database returns an empty list. """
    # Arrange
    skip, limit = 0, 50
    mock_list.return_value = [] # Simulate empty result

    # Act
    result = await asset_service.list_assets(db=db_session, skip=skip, limit=limit)

    # Assert
    mock_list.assert_called_once_with(db=db_session, skip=skip, limit=limit)
    assert result == []
