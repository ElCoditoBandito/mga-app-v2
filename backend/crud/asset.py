# backend/crud/asset.py

import uuid
from typing import Sequence, Dict, Any
from datetime import date # Added for option details
from decimal import Decimal # Added for option details

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # Import selectinload

from backend.models import Asset
# Added OptionType
from backend.models.enums import AssetType, OptionType, Currency # Keep AssetType/OptionType for potential use if needed
# No longer need specific create schemas here for create_asset
from backend.schemas import AssetUpdate


async def create_asset(
    db: AsyncSession, *, asset_data: Dict[str, Any] # Accept a dictionary with all needed data
) -> Asset:
    """
    Creates a new asset based on the provided data dictionary.
    This function expects asset_data to contain all necessary fields
    (symbol, name, currency, asset_type, option fields if applicable, etc.)
    pre-processed by a service layer.
    """
    # Ensure symbol consistency (should ideally be handled by service layer too)
    if 'symbol' in asset_data and asset_data['symbol']:
        asset_data['symbol'] = asset_data['symbol'].upper()

    # Directly create the Asset model instance from the provided dictionary
    # Assumes asset_data contains valid keys/values matching Asset model fields
    db_obj = Asset(**asset_data)

    db.add(db_obj)
    await db.flush() # Use flush instead of commit within CRUD for potential transaction management by service layer

    # **FIX:** Explicitly refresh to load relationships like underlying_asset if applicable
    # This helps prevent lazy loading issues later.
    refresh_attributes = []
    if db_obj.asset_type == AssetType.OPTION and db_obj.underlying_asset_id:
        refresh_attributes.append('underlying_asset')
    # Add other relationships here if needed in the future

    if refresh_attributes:
        await db.refresh(db_obj, attribute_names=refresh_attributes)
    else:
         await db.refresh(db_obj) # Refresh basic attributes

    return db_obj


async def get_asset(db: AsyncSession, asset_id: uuid.UUID) -> Asset | None:
    """Gets an asset by its ID."""
    # **FIX:** Eager load underlying_asset when fetching single asset
    result = await db.execute(
        select(Asset)
        .options(selectinload(Asset.underlying_asset)) # Eager load
        .filter(Asset.id == asset_id)
    )
    return result.unique().scalars().first()


async def get_asset_by_symbol(db: AsyncSession, symbol: str) -> Asset | None:
    """Gets an asset by its symbol (case-insensitive)."""
    # **FIX:** Eager load underlying_asset when fetching by symbol
    result = await db.execute(
        select(Asset)
        .options(selectinload(Asset.underlying_asset)) # Eager load
        .filter(Asset.symbol == symbol.upper())
    )
    return result.unique().scalars().first()


# --- NEW FUNCTION ---
async def get_option_by_contract_details(
    db: AsyncSession,
    *, # Enforce keyword arguments
    underlying_asset_id: uuid.UUID,
    option_type: OptionType,
    strike_price: Decimal,
    expiration_date: date
) -> Asset | None:
    """
    Retrieves a specific option asset based on its defining contract details.

    Uses the fields that form the unique constraint for options.

    Args:
        db: The AsyncSession instance.
        underlying_asset_id: The ID of the underlying stock asset.
        option_type: The type of option (CALL or PUT).
        strike_price: The strike price of the option.
        expiration_date: The expiration date of the option.

    Returns:
        The Asset model instance if found, otherwise None.
    """
    stmt = select(Asset).where(
        Asset.asset_type == AssetType.OPTION,
        Asset.underlying_asset_id == underlying_asset_id,
        Asset.option_type == option_type,
        Asset.strike_price == strike_price,
        Asset.expiration_date == expiration_date
    ).options(selectinload(Asset.underlying_asset)) # Eager load here too
    result = await db.execute(stmt)
    return result.unique().scalars().first()
# --- END NEW FUNCTION ---


async def get_multi_assets(
    db: AsyncSession, *, skip: int = 0, limit: int = 100
) -> Sequence[Asset]:
    """Gets multiple assets with pagination."""
    # **FIX:** Eager load underlying_asset when fetching multiple assets
    result = await db.execute(
        select(Asset)
        .options(selectinload(Asset.underlying_asset)) # Eager load
        .offset(skip)
        .limit(limit)
        .order_by(Asset.symbol, Asset.id)
    )
    return result.unique().scalars().all()


async def update_asset(
    db: AsyncSession, *, db_obj: Asset, obj_in: AssetUpdate
) -> Asset:
    """Updates an asset based on the AssetUpdate schema."""
    # Decide which fields are updatable. Symbol and type usually are not.
    update_data = obj_in.model_dump(exclude_unset=True)

    # Explicitly prevent updating immutable fields if AssetUpdate allows them
    update_data.pop('symbol', None)
    update_data.pop('asset_type', None)
    update_data.pop('underlying_asset_id', None)
    update_data.pop('option_type', None)
    update_data.pop('strike_price', None)
    update_data.pop('expiration_date', None)


    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    await db.flush() # Use flush
    # Refresh potentially updated fields and relationships if needed
    refresh_attributes = []
    if db_obj.asset_type == AssetType.OPTION and db_obj.underlying_asset_id:
        refresh_attributes.append('underlying_asset')
    if refresh_attributes:
        await db.refresh(db_obj, attribute_names=refresh_attributes)
    else:
        await db.refresh(db_obj)
    return db_obj


async def delete_asset(db: AsyncSession, *, db_obj: Asset) -> Asset:
    """Deletes an asset."""
    # Consider implications: Check if Positions exist for this asset?
    # Might prevent deletion or require marking as inactive instead (service layer).
    # Assuming direct delete for now.
    await db.delete(db_obj)
    await db.flush() # Use flush
    # Returning the object after delete might be useful for logging, but it's detached.
    return db_obj
