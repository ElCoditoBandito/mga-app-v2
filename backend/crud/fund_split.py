# backend/crud/fund_split.py

import uuid
from typing import Sequence, Dict, Any # Import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import FundSplit # SQLAlchemy Model
# Import only schemas needed for update/read
from backend.schemas import FundSplitUpdate # Removed FundSplitCreate


async def create_fund_split(db: AsyncSession, *, fund_split_data: Dict[str, Any]) -> FundSplit:
    """
    Creates a new fund split record (Club Level).
    Expects fund_split_data dict containing 'club_id', 'fund_id',
    and 'split_percentage'.
    """
    # Filter data to match model attributes
    model_data = {k: v for k, v in fund_split_data.items() if hasattr(FundSplit, k)}

    # Optional check for required fields (service layer should ensure this)
    required_fields = ['club_id', 'fund_id', 'split_percentage']
    if not all(k in model_data for k in required_fields):
        raise ValueError("Missing required fields for FundSplit model")

    # Create the SQLAlchemy model instance
    db_obj = FundSplit(**model_data)

    db.add(db_obj)
    await db.flush()
    await db.refresh(db_obj)
    return db_obj


async def get_fund_split(db: AsyncSession, fund_split_id: uuid.UUID) -> FundSplit | None:
    """Gets a fund split by its ID."""
    result = await db.execute(select(FundSplit).filter(FundSplit.id == fund_split_id))
    return result.unique().scalars().first() # Added unique()

# Function to get splits by membership is no longer applicable
# async def get_fund_splits_by_membership(...)

async def get_fund_splits_by_fund(
    db: AsyncSession, *, fund_id: uuid.UUID, club_id: uuid.UUID | None = None # Added optional club_id filter
) -> Sequence[FundSplit]:
    """Gets all fund splits associated with a given fund (optionally filtered by club)."""
    stmt = select(FundSplit).filter(FundSplit.fund_id == fund_id)
    if club_id:
        stmt = stmt.filter(FundSplit.club_id == club_id)
    stmt = stmt.order_by(FundSplit.club_id) # Order by club
    result = await db.execute(stmt)
    return result.unique().scalars().all() # Added unique()

async def get_fund_splits_by_club( # New helper function might be useful
    db: AsyncSession, *, club_id: uuid.UUID
) -> Sequence[FundSplit]:
    """Gets all fund splits for a given club."""
    stmt = select(FundSplit).filter(FundSplit.club_id == club_id).order_by(FundSplit.fund_id)
    result = await db.execute(stmt)
    return result.unique().scalars().all() # Added unique()


async def get_multi_fund_splits(
    db: AsyncSession, *, skip: int = 0, limit: int = 100, club_id: uuid.UUID | None = None, fund_id: uuid.UUID | None = None
) -> Sequence[FundSplit]:
    """Gets multiple fund splits with pagination and optional filtering."""
    stmt = select(FundSplit)
    # Removed membership_id filter
    if club_id:
        stmt = stmt.filter(FundSplit.club_id == club_id)
    if fund_id:
        stmt = stmt.filter(FundSplit.fund_id == fund_id)

    stmt = stmt.offset(skip).limit(limit).order_by(FundSplit.club_id, FundSplit.fund_id, FundSplit.id) # Adjusted order
    result = await db.execute(stmt)
    return result.unique().scalars().all() # Added unique()


async def update_fund_split(
    db: AsyncSession, *, db_obj: FundSplit, obj_in: FundSplitUpdate
) -> FundSplit:
    """Updates a fund split (likely just the percentage)."""
    # Use the FundSplitUpdate schema which should define the updatable fields
    update_data = obj_in.model_dump(exclude_unset=True)

    # Explicitly prevent changing keys if necessary, although schema should control this
    update_data.pop('fund_id', None)
    update_data.pop('club_id', None)

    for field, value in update_data.items():
        if hasattr(db_obj, field):
             setattr(db_obj, field, value)

    db.add(db_obj)
    await db.flush()
    await db.refresh(db_obj)
    return db_obj


async def delete_fund_split(db: AsyncSession, *, db_obj: FundSplit) -> FundSplit:
    """Deletes a fund split."""
    await db.delete(db_obj)
    await db.flush()
    return db_obj
