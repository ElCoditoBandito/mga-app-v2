# backend/crud/member_transaction.py

import uuid
from datetime import datetime # Use datetime
from typing import Sequence, Dict, Any # Import Dict, Any
from decimal import Decimal # Import Decimal

from sqlalchemy import select, desc, func, join # Import desc, func, join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload # Import aliased if needed for joins, selectinload

# Import models needed for join
from backend.models import MemberTransaction, ClubMembership, User, Club # Added User, Club
from backend.models.enums import MemberTransactionType # Keep for potential logic

# Member Transactions (deposits/withdrawals) are typically immutable.
# Corrections usually involve creating reversal/adjusting transactions.

async def create_member_transaction(
    db: AsyncSession, *, member_tx_data: Dict[str, Any] # Accept dictionary
) -> MemberTransaction:
    """
    Creates a new member transaction (deposit/withdrawal) record.
    Expects member_tx_data dict containing 'membership_id', 'transaction_type',
    'amount', 'transaction_date', and potentially 'notes', 'unit_value_used', 'units_transacted'.
    """
    # Filter data to match model attributes
    model_data = {k: v for k, v in member_tx_data.items() if hasattr(MemberTransaction, k)}

    # Create the SQLAlchemy model instance
    db_obj = MemberTransaction(**model_data)

    db.add(db_obj)
    await db.flush()
    # Refresh to load server-defaults and potentially relationships if needed immediately
    await db.refresh(db_obj, attribute_names=['id', 'created_at', 'updated_at'])
    return db_obj


async def get_member_transaction(
    db: AsyncSession, member_transaction_id: uuid.UUID
) -> MemberTransaction | None:
    """Gets a member transaction by its ID, loading necessary relationships."""
    # Use select() with options as the Read schema likely needs nested data
    stmt = select(MemberTransaction).where(MemberTransaction.id == member_transaction_id).options(
        selectinload(MemberTransaction.membership).selectinload(ClubMembership.user),
        selectinload(MemberTransaction.membership).selectinload(ClubMembership.club)
    )
    result = await db.execute(stmt)
    return result.unique().scalars().first()
    # Alternative using db.get if relationships are not needed:
    # result = await db.get(MemberTransaction, member_transaction_id)
    # return result


async def get_multi_member_transactions(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
    membership_id: uuid.UUID | None = None,
    club_id: uuid.UUID | None = None # Filter by club_id
) -> Sequence[MemberTransaction]:
    """
    Gets multiple member transactions with pagination, optionally filtered by membership OR club.
    If club_id is provided, it retrieves all member transactions for that club.
    If membership_id is provided, it retrieves transactions for that specific membership.
    Providing both is redundant (membership implies club).
    """
    stmt = select(MemberTransaction)

    if membership_id:
        stmt = stmt.filter(MemberTransaction.membership_id == membership_id)
    elif club_id:
        # Join MemberTransaction -> ClubMembership to filter by club_id
        stmt = stmt.join(
            ClubMembership, MemberTransaction.membership_id == ClubMembership.id
        ).filter(ClubMembership.club_id == club_id)

    # Eager load relationships likely needed by the Read schema
    stmt = stmt.options(
        selectinload(MemberTransaction.membership).selectinload(ClubMembership.user),
        selectinload(MemberTransaction.membership).selectinload(ClubMembership.club)
    )

    # Order by date (most recent first?), then by creation time for stability
    stmt = stmt.offset(skip).limit(limit).order_by(
        desc(MemberTransaction.transaction_date),
        desc(MemberTransaction.created_at),
        desc(MemberTransaction.id)
    )
    result = await db.execute(stmt)
    # Add unique() for safety with joins
    return result.unique().scalars().all()


# --- EXISTING FUNCTION ---
async def get_member_unit_balance(db: AsyncSession, *, membership_id: uuid.UUID) -> Decimal:
    """
    Calculates the current unit balance for a specific club membership.
    (Implementation unchanged)
    """
    stmt = select(
        func.coalesce(func.sum(MemberTransaction.units_transacted), Decimal("0.0"))
    ).where(
        MemberTransaction.membership_id == membership_id
    )
    result = await db.execute(stmt)
    total_units = result.scalar_one()
    if not isinstance(total_units, Decimal):
         return Decimal(total_units or "0.0")
    else:
         return total_units

# --- FUNCTION RENAMED in previous steps, ensure consistency ---
# This was renamed from get_total_units_for_club in the model/service layer discussion
async def get_total_units_for_club(db: AsyncSession, *, club_id: uuid.UUID) -> Decimal:
    """
    Calculates the total outstanding units for an entire club.
    (Implementation unchanged)
    """
    stmt = select(
        func.coalesce(func.sum(MemberTransaction.units_transacted), Decimal("0.0"))
    ).join(
        ClubMembership, MemberTransaction.membership_id == ClubMembership.id
    ).where(
        ClubMembership.club_id == club_id
    )
    result = await db.execute(stmt)
    total_units = result.scalar_one()
    if not isinstance(total_units, Decimal):
         return Decimal(total_units or "0.0")
    else:
         return total_units
