# backend/crud/transaction.py

import uuid
from datetime import datetime # Use datetime instead of date if schemas use it
from typing import Sequence, Dict, Any # Import Dict, Any

# Import desc, select, join for filtering/ordering
from sqlalchemy import select, desc, join
# Import models for join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # Import selectinload for potential use in get_transaction
from backend.models import Transaction, Fund # Import Fund model

from backend.models.enums import TransactionType # Import enum (might be useful for logic later)

# Transactions are typically immutable once created via API.
# Corrections usually involve creating reversal/adjusting transactions.

async def create_transaction(db: AsyncSession, *, transaction_data: Dict[str, Any]) -> Transaction:
    """
    Creates a new transaction record based on the provided data dictionary.
    Expects transaction_data dict containing all necessary fields for the Transaction model,
    pre-processed by a service layer.
    """
    # Filter data to match model attributes
    model_data = {k: v for k, v in transaction_data.items() if hasattr(Transaction, k)}

    # Create the SQLAlchemy model instance
    db_obj = Transaction(**model_data)

    db.add(db_obj)
    await db.flush()
    # Refresh to load server-defaults and potentially relationships if needed immediately
    # Consider which relationships might be needed by the caller service
    await db.refresh(db_obj, attribute_names=['id', 'created_at', 'updated_at']) # Refresh core attributes

    # Service layer would typically trigger position/fund updates after this.
    return db_obj


async def get_transaction(db: AsyncSession, transaction_id: uuid.UUID) -> Transaction | None:
    """
    Gets a transaction by its ID, potentially loading relationships.
    """
    # Use select() with options if relationships are often needed by the caller (e.g., API response)
    stmt = select(Transaction).where(Transaction.id == transaction_id).options(
        selectinload(Transaction.fund), # Eager load fund
        selectinload(Transaction.asset) # Eager load asset
        # Add other relationships like related_transaction_link if needed
    )
    result = await db.execute(stmt)
    return result.unique().scalars().first()
    # Alternative using db.get if relationships are usually not needed immediately:
    # result = await db.get(Transaction, transaction_id)
    # return result


async def get_multi_transactions(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
    club_id: uuid.UUID | None = None, # Keep club_id filter
    fund_id: uuid.UUID | None = None, # Keep fund_id filter
    asset_id: uuid.UUID | None = None, # Keep asset_id filter
) -> Sequence[Transaction]:
    """
    Gets multiple transactions with pagination and optional filtering.
    If club_id is provided, filters transactions belonging to that club via the Fund relationship.
    """
    stmt = select(Transaction)

    # Add filters
    if club_id:
        stmt = stmt.filter(Transaction.club_id == club_id) # Filter directly on Transaction table

    if fund_id:
        stmt = stmt.filter(Transaction.fund_id == fund_id)

    if asset_id:
        stmt = stmt.filter(Transaction.asset_id == asset_id)

    # Eager load relationships likely needed by the Read schema
    stmt = stmt.options(
        selectinload(Transaction.fund),
        selectinload(Transaction.asset)
    )

    # Order by date (most recent first?), then by creation time for stability
    stmt = stmt.offset(skip).limit(limit).order_by(
        desc(Transaction.transaction_date),
        desc(Transaction.created_at),
        desc(Transaction.id)
    )
    result = await db.execute(stmt)
    # Add unique() for safety, especially with joins
    return result.unique().scalars().all()

