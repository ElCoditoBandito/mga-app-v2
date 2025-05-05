# backend/tests/crud/test_asset.py

import uuid
from datetime import date
from decimal import Decimal # Import Decimal for strike price

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Import the refactored CRUD function
from backend.crud import asset as crud_asset
from backend.models import Asset
from backend.models.enums import AssetType, OptionType, Currency
# Only AssetUpdate schema is needed for testing update
from backend.schemas import AssetUpdate

pytestmark = pytest.mark.asyncio(loop_scope="function")

# --- Helpers ---
# These helpers now prepare the data dictionary expected by the refactored CRUD function

async def create_test_stock_asset_via_crud(
    db_session: AsyncSession,
    symbol: str = "TEST",
    name: str = "Test Stock Asset",
    currency: Currency = Currency.USD,
) -> Asset:
    """Helper prepares data dict and calls refactored create_asset for STOCK."""
    asset_data = {
        "asset_type": AssetType.STOCK,
        "symbol": symbol,
        "name": name,
        "currency": currency,
        "underlying_asset_id": None,
        "option_type": None,
        "strike_price": None,
        "expiration_date": None,
    }
    # Call the refactored CRUD function with the prepared dictionary
    return await crud_asset.create_asset(db=db_session, asset_data=asset_data)


async def create_test_option_asset_via_crud(
    db_session: AsyncSession,
    underlying_asset: Asset, # Pass the created underlying asset object
    symbol: str = "TEST_OPT", # This is the option symbol
    name: str = "Test Option Asset",
    currency: Currency = Currency.USD,
    option_type: OptionType = OptionType.CALL,
    strike_price: Decimal = Decimal("100.00"), # Use Decimal
    expiration_date: date | None = None,
) -> Asset:
    """Helper prepares data dict and calls refactored create_asset for OPTION."""
    if expiration_date is None:
        expiration_date = date.today().replace(year=date.today().year + 1)

    asset_data = {
        "asset_type": AssetType.OPTION,
        "symbol": symbol, # Option's own symbol
        "name": name,
        "currency": currency,
        "underlying_asset_id": underlying_asset.id, # Link via ID
        "option_type": option_type,
        "strike_price": strike_price, # Pass Decimal
        "expiration_date": expiration_date,
    }
    # Call the refactored CRUD function with the prepared dictionary
    return await crud_asset.create_asset(db=db_session, asset_data=asset_data)


# --- Tests ---

async def test_create_asset_stock(db_session: AsyncSession):
    symbol = "AAPL"
    name = "Apple Inc."
    currency = Currency.USD

    # Use the helper which calls the refactored CRUD
    created_asset = await create_test_stock_asset_via_crud(
        db_session, symbol=symbol, name=name, currency=currency
    )

    assert created_asset is not None
    assert created_asset.symbol == symbol.upper() # CRUD handles uppercase
    assert created_asset.name == name
    assert created_asset.asset_type == AssetType.STOCK
    assert created_asset.currency == currency
    assert created_asset.id is not None
    assert created_asset.underlying_asset_id is None
    assert created_asset.option_type is None


async def test_create_asset_option(db_session: AsyncSession):
    # First, create the underlying stock using the stock helper
    underlying_stock = await create_test_stock_asset_via_crud(db_session, symbol="MSFT", name="Microsoft Corp")

    option_symbol = "MSFT_251219C300" # The symbol for the option asset itself
    option_name = "MSFT Dec 19 2025 $300 Call"
    strike = Decimal("300.00") # Use Decimal
    exp_date = date(2025, 12, 19)
    option_type = OptionType.CALL
    currency = Currency.USD

    # Use the option helper which calls the refactored CRUD
    created_option = await create_test_option_asset_via_crud(
        db_session,
        underlying_asset=underlying_stock,
        symbol=option_symbol,
        name=option_name,
        currency=currency,
        option_type=option_type,
        strike_price=strike,
        expiration_date=exp_date,
    )

    assert created_option is not None
    assert created_option.symbol == option_symbol.upper() # CRUD handles uppercase
    assert created_option.asset_type == AssetType.OPTION
    assert created_option.underlying_asset_id == underlying_stock.id
    assert created_option.option_type == option_type
    assert created_option.strike_price == strike
    assert created_option.expiration_date == exp_date
    assert created_option.currency == currency


async def test_get_asset(db_session: AsyncSession):
    # Use the stock helper to create an asset to retrieve
    created_asset = await create_test_stock_asset_via_crud(db_session, symbol="GOOG")
    retrieved_asset = await crud_asset.get_asset(db=db_session, asset_id=created_asset.id)

    assert retrieved_asset is not None
    assert retrieved_asset.id == created_asset.id
    assert retrieved_asset.symbol == "GOOG" # CRUD handles uppercase


async def test_get_asset_not_found(db_session: AsyncSession):
    non_existent_id = uuid.uuid4()
    retrieved_asset = await crud_asset.get_asset(db=db_session, asset_id=non_existent_id)
    assert retrieved_asset is None


async def test_get_asset_by_symbol(db_session: AsyncSession):
    symbol = "AMZN"
    # Use the stock helper
    created_asset = await create_test_stock_asset_via_crud(db_session, symbol=symbol)

    # Test case-insensitivity (CRUD function handles this)
    retrieved_asset = await crud_asset.get_asset_by_symbol(db=db_session, symbol="amzn")

    assert retrieved_asset is not None
    assert retrieved_asset.id == created_asset.id
    assert retrieved_asset.symbol == symbol.upper()


async def test_get_asset_by_symbol_not_found(db_session: AsyncSession):
    retrieved_asset = await crud_asset.get_asset_by_symbol(db=db_session, symbol="NOSUCH")
    assert retrieved_asset is None


async def test_get_multi_assets(db_session: AsyncSession):
    # Use the stock helper
    asset1 = await create_test_stock_asset_via_crud(db_session, symbol="TSLA")
    asset2 = await create_test_stock_asset_via_crud(db_session, symbol="NVDA")
    asset3 = await create_test_stock_asset_via_crud(db_session, symbol="IBM")

    # Test pagination (order by symbol: IBM, NVDA, TSLA)
    assets_page1 = await crud_asset.get_multi_assets(db=db_session, skip=0, limit=2)
    assert len(assets_page1) == 2
    assert {a.id for a in assets_page1} == {asset3.id, asset2.id} # IBM, NVDA

    assets_page2 = await crud_asset.get_multi_assets(db=db_session, skip=1, limit=2)
    assert len(assets_page2) == 2
    assert {a.id for a in assets_page2} == {asset2.id, asset1.id} # NVDA, TSLA


async def test_update_asset(db_session: AsyncSession):
    # Use the stock helper
    created_asset = await create_test_stock_asset_via_crud(db_session, symbol="DELL", name="Dell Inc")

    # AssetUpdate schema only allows name and currency
    update_data = AssetUpdate(name="Dell Technologies")
    updated_asset = await crud_asset.update_asset(
        db=db_session, db_obj=created_asset, obj_in=update_data
    )

    assert updated_asset is not None
    assert updated_asset.id == created_asset.id
    assert updated_asset.symbol == "DELL" # Symbol shouldn't change
    assert updated_asset.name == "Dell Technologies"

    refetched = await crud_asset.get_asset(db=db_session, asset_id=created_asset.id)
    assert refetched.name == "Dell Technologies"


async def test_delete_asset(db_session: AsyncSession):
    # Use the stock helper
    created_asset = await create_test_stock_asset_via_crud(db_session, symbol="ORCL")
    asset_id = created_asset.id

    deleted_asset = await crud_asset.delete_asset(db=db_session, db_obj=created_asset)
    assert deleted_asset.id == asset_id

    retrieved = await crud_asset.get_asset(db=db_session, asset_id=asset_id)
    assert retrieved is None


async def test_create_duplicate_asset_stock_symbol_fails(db_session: AsyncSession):
    # This test relies on the partial unique index 'uq_asset_stock_symbol'
    symbol = "UNIQUE"
    # Use the stock helper
    await create_test_stock_asset_via_crud(db_session, symbol=symbol)

    # Try creating another stock asset with the same symbol using the helper
    with pytest.raises(IntegrityError): # Expect DB constraint violation
         await create_test_stock_asset_via_crud(db_session, symbol=symbol.lower(), name="Duplicate")


async def test_create_duplicate_option_contract_fails(db_session: AsyncSession):
    # This test relies on the partial unique index 'uq_asset_option_contract'
    underlying = await create_test_stock_asset_via_crud(db_session, symbol="DUPOPT")
    exp_date = date(2026, 1, 16)
    strike = Decimal("50.00") # Use Decimal
    opt_type = OptionType.PUT

    # Create first option
    await create_test_option_asset_via_crud(
        db_session, underlying, symbol="DUPOPT_OPT1", option_type=opt_type, strike_price=strike, expiration_date=exp_date
    )

    # Try creating identical option contract (same underlying, type, strike, expiry)
    with pytest.raises(IntegrityError):
        await create_test_option_asset_via_crud(
            db_session, underlying, symbol="DUPOPT_OPT2", option_type=opt_type, strike_price=strike, expiration_date=exp_date
        )

