# backend/crud/unit_value_history.py

import uuid
from datetime import date, datetime # Import datetime if needed for created_at/updated_at
from decimal import Decimal
from typing import Sequence, Dict, Any # Import Dict, Any

# Added asc for ordering
from sqlalchemy import select, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import UnitValueHistory # SQLAlchemy Model
# No schemas needed for this CRUD module typically

# UnitValueHistory records are typically created periodically by internal logic.

async def create_unit_value_history(
    db: AsyncSession,
    *, # Enforce keyword arguments
    uvh_data: Dict[str, Any] # Accept dictionary
) -> UnitValueHistory:
    """
    Creates a new unit value history record (intended for internal use).
    Expects uvh_data dict containing 'club_id', 'valuation_date',
    'total_club_value', 'total_units_outstanding', 'unit_value'.
    """
    # Filter data to match model attributes
    model_data = {k: v for k, v in uvh_data.items() if hasattr(UnitValueHistory, k)}

    # Optional check for required fields
    required_fields = ['club_id', 'valuation_date', 'total_club_value', 'total_units_outstanding', 'unit_value']
    if not all(k in model_data for k in required_fields):
        raise ValueError("Missing required fields for UnitValueHistory model")

    # Create the SQLAlchemy model instance
    db_obj = UnitValueHistory(**model_data)
    db.add(db_obj)
    await db.flush()
    await db.refresh(db_obj)
    return db_obj


async def get_unit_value_history(
    db: AsyncSession, unit_value_history_id: uuid.UUID
) -> UnitValueHistory | None:
    """Gets a unit value history record by its ID."""
    result = await db.execute(
        select(UnitValueHistory).filter(UnitValueHistory.id == unit_value_history_id)
    )
    # Add unique() for safety
    return result.unique().scalars().first()


async def get_latest_unit_value_for_club( # Renamed function
    db: AsyncSession, *, club_id: uuid.UUID # Filter by club_id
) -> UnitValueHistory | None:
    """Gets the most recent unit value history record for a given club."""
    result = await db.execute(
        select(UnitValueHistory)
        .filter(UnitValueHistory.club_id == club_id) # Use club_id
        # Use correct column name valuation_date
        .order_by(desc(UnitValueHistory.valuation_date), desc(UnitValueHistory.created_at), desc(UnitValueHistory.id))
        .limit(1)
    )
    # Add unique() for safety
    return result.unique().scalars().first()


async def get_multi_unit_value_history(
    db: AsyncSession, *, skip: int = 0, limit: int = 100, club_id: uuid.UUID | None = None # Filter by club_id
) -> Sequence[UnitValueHistory]:
    """Gets multiple unit value history records with pagination, optionally filtered by club."""
    stmt = select(UnitValueHistory)
    if club_id:
        stmt = stmt.filter(UnitValueHistory.club_id == club_id) # Use club_id

    # Order by correct column name valuation_date
    stmt = stmt.offset(skip).limit(limit).order_by(
        desc(UnitValueHistory.valuation_date),
        desc(UnitValueHistory.created_at),
        desc(UnitValueHistory.id)
    )
    result = await db.execute(stmt)
    # Add unique() for safety
    return result.unique().scalars().all()


# --- NEW FUNCTION ---
async def get_unit_value_history_for_period(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    start_date: date,
    end_date: date
) -> Sequence[UnitValueHistory]:
    """
    Retrieves unit value history records for a specific club within a given date range.

    Args:
        db: The AsyncSession instance.
        club_id: The ID of the club.
        start_date: The start date of the period (inclusive).
        end_date: The end date of the period (inclusive).

    Returns:
        A sequence of UnitValueHistory records ordered by valuation_date ascending.
    """
    stmt = select(UnitValueHistory).where(
        UnitValueHistory.club_id == club_id,
        UnitValueHistory.valuation_date >= start_date,
        UnitValueHistory.valuation_date <= end_date
    ).order_by(
        asc(UnitValueHistory.valuation_date) # Order chronologically
    )
    result = await db.execute(stmt)
    return result.unique().scalars().all()
# --- END NEW FUNCTION ---


async def delete_unit_value_history(
    db: AsyncSession, *, db_obj: UnitValueHistory
) -> UnitValueHistory:
    """
    Deletes a unit value history record (potentially for internal correction logic).
    """
    await db.delete(db_obj)
    await db.flush()
    return db_obj

