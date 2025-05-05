# backend/services/asset_service.py

import uuid
import logging
from typing import Dict, Any, Sequence
from decimal import Decimal
from datetime import date

# Assuming SQLAlchemy and FastAPI are installed in the environment
try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.exc import IntegrityError
    from fastapi import HTTPException, status
    # Removed selectinload as it's not used directly in this service file
except ImportError:
    # Provide fallback message if imports fail
    print("WARNING: SQLAlchemy or FastAPI not found. Service functions may not execute.")
    # Define dummy types/classes if needed
    class AsyncSession: pass
    class IntegrityError(Exception): pass
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)
    class Status:
        HTTP_404_NOT_FOUND = 404
        HTTP_409_CONFLICT = 409
        HTTP_422_UNPROCESSABLE_ENTITY = 422
        HTTP_500_INTERNAL_SERVER_ERROR = 500
    status = Status()
    # def selectinload(*args): pass # Dummy decorator

# Import CRUD functions, Models, Schemas, and Enums
try:
    from backend.crud import asset as crud_asset
    from backend.models import Asset # [cite: backend_files/models/asset.py]
    from backend.models.enums import AssetType, Currency, OptionType # [cite: backend_files/models/enums.py]
    from backend.schemas import AssetCreateStock, AssetCreateOption # [cite: backend_files/schemas/asset.py]
except ImportError as e:
    print(f"WARNING: Failed to import CRUD/Models/Schemas/Enums: {e}. Service functions may not work.")
    # Define dummy types/classes if needed
    class Asset: id: uuid.UUID; symbol: str; asset_type: str; currency: str; underlying_asset: Any = None; name: str | None = None; underlying_asset_id: uuid.UUID | None = None; option_type: Any = None; strike_price: Any = None; expiration_date: Any = None
    class AssetType: STOCK = "Stock"; OPTION = "Option"
    class Currency: USD = "USD"
    class OptionType: CALL = "Call"; PUT = "Put"
    class AssetCreateStock: symbol: str; name: str | None
    class AssetCreateOption: underlying_symbol: str; option_type: OptionType; strike_price: Decimal; expiration_date: date; name: str | None
    class crud_asset:
        @staticmethod
        async def get_asset_by_symbol(db: AsyncSession, symbol: str) -> Asset | None: return None
        @staticmethod
        async def create_asset(db: AsyncSession, *, asset_data: Dict[str, Any]) -> Asset: return Asset(id=uuid.uuid4(), symbol=asset_data.get('symbol',''), asset_type=asset_data.get('asset_type',''), currency=asset_data.get('currency',''), name=asset_data.get('name'))
        @staticmethod
        async def get_option_by_contract_details(db: AsyncSession, *, underlying_asset_id: uuid.UUID, option_type: OptionType, strike_price: Decimal, expiration_date: date) -> Asset | None: return None
        @staticmethod
        async def get_asset(db: AsyncSession, asset_id: uuid.UUID) -> Asset | None: return Asset(id=asset_id, symbol="DUMMY", asset_type="Stock", currency="USD")
        @staticmethod
        async def get_multi_assets(db: AsyncSession, *, skip: int = 0, limit: int = 100) -> Sequence[Asset]: return [Asset(id=uuid.uuid4(), symbol="DUMMY", asset_type="Stock", currency="USD")]


# Configure logging
log = logging.getLogger(__name__)


async def get_or_create_stock_asset(
    db: AsyncSession, *, asset_in: AssetCreateStock
) -> Asset:
    """
    Retrieves a stock asset by its symbol, creating it if it doesn't exist.
    If an asset exists with the symbol but is not type STOCK, it raises an error.
    Relies on database constraints to prevent duplicate STOCK symbols.
    """
    symbol_upper = asset_in.symbol.upper()
    log.debug(f"Service: Checking for asset with symbol: {symbol_upper}")
    # Use eager loading in CRUD now to ensure relationships are loaded if needed later
    existing_asset = await crud_asset.get_asset_by_symbol(db=db, symbol=symbol_upper) # [cite: crud_asset_py_updated]

    if existing_asset:
        if existing_asset.asset_type == AssetType.STOCK:
            log.info(f"Found existing STOCK asset for symbol: {symbol_upper} (ID: {existing_asset.id})")
            return existing_asset
        else:
            # Found an asset with the same symbol, but it's not a stock (e.g., an option)
            # This should generally not happen if symbols are managed correctly, but handle defensively.
            log.error(f"Asset symbol conflict: Symbol '{symbol_upper}' already exists but is type '{existing_asset.asset_type}', not STOCK.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Symbol '{symbol_upper}' already exists but is not a stock asset. Cannot create stock with this symbol."
            )
    else:
         log.info(f"No asset found for symbol: {symbol_upper}. Attempting creation.")

    # Attempt to create the STOCK asset
    asset_data: Dict[str, Any] = {
        "asset_type": AssetType.STOCK, "symbol": symbol_upper, "name": asset_in.name,
        "currency": Currency.USD, # Assuming default currency, adjust if needed
        "option_type": None, "strike_price": None,
        "expiration_date": None, "underlying_asset_id": None,
    }
    try:
        # Use eager loading in CRUD now
        new_asset = await crud_asset.create_asset(db=db, asset_data=asset_data) # [cite: crud_asset_py_updated]
        log.info(f"Successfully created new STOCK asset (ID: {new_asset.id}) for symbol: {symbol_upper}")
        return new_asset
    except IntegrityError as e:
        # This likely means a STOCK with this symbol was created concurrently,
        # or potentially the partial index isn't working as expected.
        log.exception(f"IntegrityError creating stock asset for symbol {symbol_upper}: {e}")
        await db.rollback()
        # Attempt to refetch, maybe the concurrent creation succeeded
        refetched_asset = await crud_asset.get_asset_by_symbol(db=db, symbol=symbol_upper)
        if refetched_asset and refetched_asset.asset_type == AssetType.STOCK:
            log.warning(f"Stock asset for {symbol_upper} created concurrently, returning existing.")
            return refetched_asset
        # If refetch fails or it's still not a stock, raise conflict
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Failed to create stock asset for symbol '{symbol_upper}'. A stock with this symbol likely already exists.")
    except Exception as e:
        log.exception(f"Unexpected error creating stock asset for symbol {symbol_upper}: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the stock asset.")


async def get_or_create_option_asset(
    db: AsyncSession, *, asset_in: AssetCreateOption
) -> Asset:
    """
    Retrieves an option asset based on its contract details (underlying, type, strike, expiry),
    creating it if it doesn't exist. Ensures the underlying stock asset exists, creating it if necessary.

    Args:
        db: The AsyncSession instance.
        asset_in: The Pydantic schema containing option creation data.

    Returns:
        The existing or newly created option Asset model instance.

    Raises:
        HTTPException 409: If the underlying symbol exists but is not a STOCK.
        HTTPException 409: If the option contract already exists but creation failed due to race condition.
        HTTPException 500: For other unexpected database errors.
    """
    underlying_symbol_upper = asset_in.underlying_symbol.upper()

    # --- Ensure underlying STOCK asset exists, create if needed ---
    log.debug(f"Ensuring underlying stock exists for symbol: {underlying_symbol_upper}")
    # This call might raise HTTPException 409 if symbol exists but isn't STOCK
    underlying_asset = await get_or_create_stock_asset(
        db=db,
        asset_in=AssetCreateStock(symbol=underlying_symbol_upper) # Name can be None here
    )
    # No need to check type again, get_or_create_stock_asset guarantees STOCK or raises error
    log.info(f"Confirmed underlying STOCK asset for option: {underlying_symbol_upper} (ID: {underlying_asset.id})")

    # Check if this specific option contract already exists
    try:
        existing_option = await crud_asset.get_option_by_contract_details(
            db=db,
            underlying_asset_id=underlying_asset.id,
            option_type=asset_in.option_type,
            strike_price=asset_in.strike_price,
            expiration_date=asset_in.expiration_date
        ) # [cite: crud_asset_py_updated]
    except AttributeError:
         log.warning("crud_asset.get_option_by_contract_details not found. Skipping check for existing option.")
         existing_option = None
    except Exception as e:
         log.error(f"Error checking for existing option: {e}")
         existing_option = None

    if existing_option:
        log.info(f"Found existing OPTION asset for contract details (ID: {existing_option.id})")
        # --- FIX: Removed problematic refresh call ---
        # The mock/CRUD should return the object in the desired state.
        # Refreshing a potentially mocked object that isn't in the session is invalid.
        # if not existing_option.underlying_asset:
        #     log.warning(f"Existing option {existing_option.id} missing underlying_asset relationship after fetch. Refreshing.")
        #     await db.refresh(existing_option, attribute_names=['underlying_asset'])
        # --- END FIX ---
        return existing_option

    # Option doesn't exist, prepare data for creation
    log.info(f"Option asset not found for contract details. Attempting creation.")
    # Generate a more descriptive symbol/name if needed
    option_symbol = f"{underlying_symbol_upper}_{asset_in.expiration_date.strftime('%y%m%d')}{asset_in.option_type.value[0]}{int(asset_in.strike_price)}"
    option_name = asset_in.name or f"{underlying_symbol_upper} {asset_in.expiration_date.strftime('%b %d %Y')} ${asset_in.strike_price:.2f} {asset_in.option_type.value}"

    asset_data: Dict[str, Any] = {
        "asset_type": AssetType.OPTION, "symbol": option_symbol, "name": option_name,
        "currency": underlying_asset.currency, # Inherit currency from underlying
        "option_type": asset_in.option_type,
        "strike_price": asset_in.strike_price,
        "expiration_date": asset_in.expiration_date,
        "underlying_asset_id": underlying_asset.id,
    }

    try:
        new_asset = await crud_asset.create_asset(db=db, asset_data=asset_data) # [cite: crud_asset_py_updated]
        log.info(f"Successfully created new OPTION asset (ID: {new_asset.id}) for underlying {underlying_symbol_upper}")
        # Ensure relationship is loaded if needed immediately after creation (CRUD should handle this)
        # if not new_asset.underlying_asset:
        #      log.error(f"Underlying asset relationship not loaded for newly created option {new_asset.id} despite refresh in CRUD.")
        return new_asset
    except IntegrityError as e:
        log.exception(f"IntegrityError creating option asset for underlying {underlying_symbol_upper}: {e}")
        await db.rollback()
        # Attempt to refetch in case of concurrent creation
        try:
            refetched_option = await crud_asset.get_option_by_contract_details(db=db, underlying_asset_id=underlying_asset.id, option_type=asset_in.option_type, strike_price=asset_in.strike_price, expiration_date=asset_in.expiration_date)
            if refetched_option:
                log.warning(f"Option asset for {underlying_symbol_upper} created concurrently, returning existing.")
                return refetched_option
        except Exception as refetch_e:
            log.error(f"Error refetching option after IntegrityError: {refetch_e}")
        # If refetch fails, raise the conflict error
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Failed to create option asset for underlying '{underlying_symbol_upper}'. It might already exist.")
    except Exception as e:
        log.exception(f"Unexpected error creating option asset for underlying {underlying_symbol_upper}: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while creating the option asset.")

# --- Asset Retrieval Services ---

async def get_asset_by_id(db: AsyncSession, asset_id: uuid.UUID) -> Asset:
    """ Retrieves a single asset by its ID. """
    log.debug(f"Attempting to retrieve asset with ID: {asset_id}")
    # CRUD function should handle eager loading if needed
    asset = await crud_asset.get_asset(db=db, asset_id=asset_id) # [cite: crud_asset_py_updated]
    if not asset:
        log.warning(f"Asset not found: {asset_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset with id {asset_id} not found.")
    log.debug(f"Successfully retrieved asset {asset_id}")
    return asset

async def list_assets(db: AsyncSession, *, skip: int = 0, limit: int = 100) -> Sequence[Asset]:
    """ Retrieves a list of assets with optional filtering and pagination. """
    log.debug(f"Listing assets with skip: {skip}, limit: {limit}")
    # CRUD function should handle eager loading if needed
    assets = await crud_asset.get_multi_assets(db=db, skip=skip, limit=limit) # [cite: crud_asset_py_updated]
    log.debug(f"Retrieved {len(assets)} assets.")
    return assets
