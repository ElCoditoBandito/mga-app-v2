# backend/crud/fund.py

import uuid
from typing import Sequence, Dict, Any # Import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Fund
# Import only schemas needed for update/read
from backend.schemas import FundUpdate # Removed FundCreate


async def create_fund(db: AsyncSession, *, fund_data: Dict[str, Any]) -> Fund:
    """
    Creates a new fund record in the database.
    Expects fund_data dict containing 'club_id', 'name', 'description', etc.
    """
    # Ensure required keys are present (optional, service layer should guarantee)
    # if not all(k in fund_data for k in ['club_id', 'name']):
    #     raise ValueError("Missing required fields ('club_id', 'name') in fund_data")

    db_obj = Fund(
        club_id=fund_data.get("club_id"),
        name=fund_data.get("name"),
        description=fund_data.get("description"),
        # Set other fields if provided, e.g., initial cash balance
        brokerage_cash_balance=fund_data.get("brokerage_cash_balance", 0.00),
        is_active=fund_data.get("is_active", True)
    )
    db.add(db_obj)
    await db.flush()
    await db.refresh(db_obj)
    return db_obj


async def get_fund(db: AsyncSession, fund_id: uuid.UUID) -> Fund | None:
    """Gets a fund by its ID."""
    result = await db.execute(select(Fund).filter(Fund.id == fund_id))
    # Add unique() for safety
    return result.unique().scalars().first()


async def get_fund_by_club_and_name(
    db: AsyncSession, *, club_id: uuid.UUID, name: str
) -> Fund | None:
    """Gets a fund by its club ID and name."""
    result = await db.execute(
        select(Fund).filter(Fund.club_id == club_id, Fund.name == name)
    )
    # Add unique() for safety
    return result.unique().scalars().first()


async def get_multi_funds(
    db: AsyncSession, *, skip: int = 0, limit: int = 100, club_id: uuid.UUID | None = None
) -> Sequence[Fund]:
    """Gets multiple funds with pagination, optionally filtered by club."""
    stmt = select(Fund)
    if club_id:
        stmt = stmt.filter(Fund.club_id == club_id)

    stmt = stmt.offset(skip).limit(limit).order_by(Fund.name, Fund.id)
    result = await db.execute(stmt)
    # Add unique() for safety
    return result.unique().scalars().all()


async def update_fund(
    db: AsyncSession, *, db_obj: Fund, obj_in: FundUpdate
) -> Fund:
    """Updates a fund."""
    update_data = obj_in.model_dump(exclude_unset=True)
    # Prevent changing club_id if necessary
    update_data.pop('club_id', None)

    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    await db.flush()
    await db.refresh(db_obj)
    return db_obj


async def delete_fund(db: AsyncSession, *, db_obj: Fund) -> Fund:
    """Deletes a fund."""
    # Consider implications: Are there Positions, FundSplits, Transactions?
    # Deletion might fail due to FK constraints or require cascade.
    # For testing, assume direct delete is possible if no dependencies created.
    await db.delete(db_obj)
    await db.flush()
    return db_obj
