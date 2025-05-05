# backend/crud/club_membership.py

import uuid
from typing import Sequence, Dict, Any # Import Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import ClubMembership
from backend.models.enums import ClubRole
# Import only schemas needed for update/read
from backend.schemas import ClubMembershipUpdate # Removed ClubMembershipCreate


async def create_club_membership(
    db: AsyncSession, *, membership_data: Dict[str, Any] # Accept a dictionary
) -> ClubMembership:
    """
    Creates a new club membership record in the database.
    Expects membership_data dict containing 'user_id', 'club_id', 'role'.
    """
    # Ensure required keys are present (optional, service layer should guarantee)
    # if not all(k in membership_data for k in ['user_id', 'club_id', 'role']):
    #     raise ValueError("Missing required fields ('user_id', 'club_id', 'role') in membership_data")

    # Use get with default for role if service layer might omit it
    db_obj = ClubMembership(
        user_id=membership_data.get("user_id"),
        club_id=membership_data.get("club_id"),
        role=membership_data.get("role", ClubRole.MEMBER), # Default if not provided
    )
    db.add(db_obj)
    await db.flush()
    await db.refresh(db_obj)
    return db_obj


async def get_club_membership(
    db: AsyncSession, membership_id: uuid.UUID
) -> ClubMembership | None:
    """Gets a club membership by its ID."""
    result = await db.execute(
        select(ClubMembership).filter(ClubMembership.id == membership_id)
    )
    # Add unique() for safety
    return result.unique().scalars().first()


async def get_club_membership_by_user_and_club(
    db: AsyncSession, *, user_id: uuid.UUID, club_id: uuid.UUID
) -> ClubMembership | None:
    """Gets a club membership by user ID and club ID."""
    result = await db.execute(
        select(ClubMembership).filter(
            ClubMembership.user_id == user_id, ClubMembership.club_id == club_id
        )
    )
    # Add unique() for safety
    return result.unique().scalars().first()


async def get_multi_club_memberships(
    db: AsyncSession, *, skip: int = 0, limit: int = 100, club_id: uuid.UUID | None = None, user_id: uuid.UUID | None = None
) -> Sequence[ClubMembership]:
    """Gets multiple club memberships with pagination and optional filtering."""
    stmt = select(ClubMembership)
    if club_id:
        stmt = stmt.filter(ClubMembership.club_id == club_id)
    if user_id:
        stmt = stmt.filter(ClubMembership.user_id == user_id)

    stmt = stmt.offset(skip).limit(limit).order_by(ClubMembership.created_at, ClubMembership.id)
    result = await db.execute(stmt)
    # Add unique() for safety
    return result.unique().scalars().all()


async def update_club_membership(
    db: AsyncSession, *, db_obj: ClubMembership, obj_in: ClubMembershipUpdate
) -> ClubMembership:
    """Updates a club membership (e.g., change role)."""
    update_data = obj_in.model_dump(exclude_unset=True)
    # Prevent changing user/club if needed
    update_data.pop('user_id', None)
    update_data.pop('club_id', None)

    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    await db.flush()
    await db.refresh(db_obj)
    return db_obj


async def delete_club_membership(
    db: AsyncSession, *, db_obj: ClubMembership
) -> ClubMembership:
    """Deletes a club membership."""
    # Consider business logic: Can the last admin be deleted? (Likely handled in service layer)
    await db.delete(db_obj)
    await db.flush()
    return db_obj
