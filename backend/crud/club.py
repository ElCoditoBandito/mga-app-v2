# backend/crud/club.py

import uuid
from typing import Sequence, Dict, Any # Import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Import models needed
from backend.models import Club, Fund, User, ClubMembership, FundSplit # Added ClubMembership, FundSplit

# Import models needed
from backend.models import Club, Fund, User # Keep Fund for get_default_fund_for_club
# Import schemas needed for update/read, not create
from backend.schemas import ClubUpdate # Removed ClubCreate


async def create_club(
    db: AsyncSession, *, club_data: Dict[str, Any] # Accept a dictionary
) -> Club:
    """
    Creates a new club record in the database.
    Expects club_data dict containing 'name', 'description', 'creator_id'.
    Creation of default fund and membership is handled by the service layer.
    """
    # Ensure required keys are present (optional, service layer should guarantee)
    # if not all(k in club_data for k in ['name', 'creator_id']):
    #     raise ValueError("Missing required fields ('name', 'creator_id') in club_data")

    db_club = Club(
        name=club_data.get("name"),
        description=club_data.get("description"),
        creator_id=club_data.get("creator_id"),
        # Set other fields from club_data if applicable (e.g., bank_account_balance)
        bank_account_balance=club_data.get("bank_account_balance", 0.00) # Example
    )
    db.add(db_club)
    await db.flush()
    await db.refresh(db_club)
    # Note: Default Fund and Creator Membership are NOT created here anymore.
    return db_club

async def get_club(db: AsyncSession, club_id: uuid.UUID) -> Club | None:
    """Gets a club by its ID, eagerly loading relationships for ClubRead schema."""
    result = await db.execute(
        select(Club)
        .options(
            selectinload(Club.memberships).selectinload(ClubMembership.user),
            selectinload(Club.funds),
            selectinload(Club.fund_splits).selectinload(FundSplit.fund)
        )
        .filter(Club.id == club_id)
    )
    # Add unique() for safety, although less likely needed than with Asset
    return result.unique().scalars().first()

async def get_club_by_name(db: AsyncSession, name: str) -> Club | None:
    """Gets a club by its name."""
    result = await db.execute(select(Club).filter(Club.name == name))
    # Add unique() for safety
    return result.unique().scalars().first()


async def get_multi_clubs(
    db: AsyncSession, *, skip: int = 0, limit: int = 100
) -> Sequence[Club]:
    """Gets multiple clubs with pagination."""
    result = await db.execute(
        select(Club).offset(skip).limit(limit).order_by(Club.name, Club.id)
    )
    # Add unique() for safety
    return result.unique().scalars().all()

async def update_club(
    db: AsyncSession, *, db_obj: Club, obj_in: ClubUpdate
) -> Club:
    """Updates a club."""
    update_data = obj_in.model_dump(exclude_unset=True)
    # Prevent updating creator_id if necessary
    update_data.pop('creator_id', None)

    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    await db.flush()
    await db.refresh(db_obj)
    return db_obj

async def delete_club(db: AsyncSession, *, db_obj: Club) -> Club:
    """Deletes a club."""
    # Note: Cascading deletes for Funds, Memberships, etc., should be configured
    # in the SQLAlchemy models or handled explicitly here if needed.
    await db.delete(db_obj)
    await db.flush()
    # The object is deleted, returning it might not be standard,
    # but useful if the caller wants the data just before deletion.
    return db_obj

# This function might still be useful for tests or services, keep it for now
async def get_default_fund_for_club(db: AsyncSession, club_id: uuid.UUID) -> Fund | None:
    """Gets the default fund for a specific club."""
    # Assuming the first fund created or a fund named "Default Fund" is the default
    result = await db.execute(
        select(Fund)
        .filter(Fund.club_id == club_id, Fund.name == "Default Fund") # Be specific
        # .order_by(Fund.created_at) # Alternative if name isn't fixed
        .limit(1)
    )
    # Add unique() for safety
    return result.unique().scalars().first()
