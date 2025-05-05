# backend/crud/position.py

import uuid
from typing import Sequence, Dict, Any # Import Dict, Any
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Position, Asset # Import Asset if needed for joins/ordering

# Note: Direct updates via API might not be standard for Position.
# Quantity/cost basis are typically modified by processing Transactions.
# CRUD functions here might be for internal use or initial setup.

async def create_position(
    db: AsyncSession,
    *, # Enforce keyword arguments
    position_data: Dict[str, Any] # Accept dictionary
) -> Position:
    """
    Creates a new position record (intended for internal use).
    Expects position_data dict containing 'fund_id', 'asset_id',
    and optionally 'quantity', 'average_cost_basis'.
    """
    # Filter data to match model attributes
    model_data = {k: v for k, v in position_data.items() if hasattr(Position, k)}

    # Set defaults if not provided (although DB model might handle this)
    model_data.setdefault('quantity', Decimal("0.0"))
    model_data.setdefault('average_cost_basis', Decimal("0.0"))

    # Optional check for required fields
    required_fields = ['fund_id', 'asset_id']
    if not all(k in model_data for k in required_fields):
        raise ValueError("Missing required fields ('fund_id', 'asset_id') for Position model")

    db_obj = Position(**model_data)
    db.add(db_obj)
    await db.flush()
    await db.refresh(db_obj)
    return db_obj


async def get_position(db: AsyncSession, position_id: uuid.UUID) -> Position | None:
    """Gets a position by its ID."""
    result = await db.execute(select(Position).filter(Position.id == position_id))
    # Add unique() for safety
    return result.unique().scalars().first()


async def get_position_by_fund_and_asset(
    db: AsyncSession, *, fund_id: uuid.UUID, asset_id: uuid.UUID
) -> Position | None:
    """Gets a position by its fund ID and asset ID."""
    result = await db.execute(
        select(Position).filter(
            Position.fund_id == fund_id, Position.asset_id == asset_id
        )
    )
    # Add unique() for safety
    return result.unique().scalars().first()


async def get_multi_positions(
    db: AsyncSession, *, skip: int = 0, limit: int = 100, fund_id: uuid.UUID | None = None
) -> Sequence[Position]:
    """Gets multiple positions with pagination, optionally filtered by fund."""
    stmt = select(Position)
    if fund_id:
        stmt = stmt.filter(Position.fund_id == fund_id)

    # Add join to Asset if sorting by symbol is desired
    # stmt = stmt.join(Position.asset) # Join Asset table
    # stmt = stmt.offset(skip).limit(limit).order_by(Asset.symbol, Position.id) # Order by Asset.symbol
    # Default sort:
    stmt = stmt.offset(skip).limit(limit).order_by(Position.created_at, Position.id)
    result = await db.execute(stmt)
    # Add unique() for safety
    return result.unique().scalars().all()


# Optional: Internal update function not tied to API Schema `PositionUpdate`
# This might be used by a service layer after processing transactions.
async def update_position_internal(
    db: AsyncSession, *, db_obj: Position, quantity_change: Decimal, cost_change: Decimal # Example args
) -> Position:
    """
    Internal helper to update position quantity and cost basis.
    Actual cost basis calculation logic resides in the service layer.
    This CRUD function just applies the pre-calculated changes.
    NOTE: This is just an example; actual implementation depends on service layer needs.
    """
    # Example: Simple additive update (real logic is more complex)
    # Ensure cost_change reflects change to average_cost_basis, not total cost
    db_obj.quantity += quantity_change
    db_obj.average_cost_basis += cost_change # Placeholder update - real calculation needed

    db.add(db_obj)
    await db.flush()
    await db.refresh(db_obj)
    return db_obj


async def delete_position(db: AsyncSession, *, db_obj: Position) -> Position:
    """Deletes a position."""
    # Usually only delete if quantity is zero and no pending transactions? (Service logic)
    # FK constraints on Transaction might prevent deletion if transactions exist.
    await db.delete(db_obj)
    await db.flush()
    return db_obj
