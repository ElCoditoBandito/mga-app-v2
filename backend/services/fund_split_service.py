# backend/services/fund_split_service.py

import uuid
import logging
from decimal import Decimal
from typing import List, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.crud import fund_split as crud_fund_split, fund as crud_fund
from backend.models import FundSplit, Fund
from backend.schemas import FundSplitItem # Use the item schema for input

log = logging.getLogger(__name__)

async def set_fund_splits_for_club(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    splits_in: List[FundSplitItem]
) -> Sequence[FundSplit]:
    """
    Sets the fund splits for a club. Deletes existing splits and creates new ones.
    Validates that percentages sum to 1.0 and funds belong to the club.

    Args:
        db: The AsyncSession instance.
        club_id: The ID of the club whose splits are being set.
        splits_in: A list of FundSplitItem schemas defining the new splits.

    Returns:
        A sequence of the newly created FundSplit model instances.

    Raises:
        HTTPException 400: If validation fails (sum != 1.0, duplicate funds, invalid funds).
        HTTPException 404: If a specified fund_id is not found or doesn't belong to the club.
        HTTPException 500: For unexpected database errors.
    """
    log.info(f"Attempting to set fund splits for club {club_id}")

    # --- Validation ---
    if not splits_in:
        # Allow clearing splits? Or require at least one?
        # For now, let's assume setting empty list clears existing splits.
        log.info(f"Received empty split list for club {club_id}. Clearing existing splits.")
        # pass # Proceed to delete existing splits
    else:
        total_percentage = sum(item.split_percentage for item in splits_in)
        # Use tolerance for floating point comparison
        if not (Decimal("0.99999") < total_percentage < Decimal("1.00001")):
            log.warning(f"Fund split percentages for club {club_id} do not sum to 1.0 (Sum: {total_percentage})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fund split percentages must sum exactly to 1.0 (100%). Current sum: {total_percentage*100:.2f}%"
            )

        fund_ids = [item.fund_id for item in splits_in]
        if len(fund_ids) != len(set(fund_ids)):
            log.warning(f"Duplicate fund IDs found in split request for club {club_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate fund IDs are not allowed in fund splits."
            )

        # Verify funds exist and belong to the club
        for item in splits_in:
            fund = await crud_fund.get_fund(db=db, fund_id=item.fund_id)
            if not fund:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fund {item.fund_id} specified in split not found.")
            if fund.club_id != club_id:
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Fund {item.fund_id} does not belong to club {club_id}.")
            if not fund.is_active:
                 log.warning(f"Attempt to set split for inactive fund {item.fund_id} in club {club_id}")
                 # Decide whether to allow splits for inactive funds - disallow for now
                 raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot set split for inactive fund {item.fund_id} ('{fund.name}').")

    # --- Execution ---
    try:
        # 1. Delete existing splits for the club
        existing_splits = await crud_fund_split.get_fund_splits_by_club(db=db, club_id=club_id)
        log.info(f"Found {len(existing_splits)} existing splits for club {club_id} to delete.")
        for split in existing_splits:
            await crud_fund_split.delete_fund_split(db=db, db_obj=split)
        if existing_splits: # Only log if something was deleted
            log.info(f"Deleted existing splits for club {club_id}.")

        # 2. Create new splits
        created_splits: List[FundSplit] = []
        if splits_in: # Only create if the input list wasn't empty
            for item in splits_in:
                split_data = {
                    "club_id": club_id,
                    "fund_id": item.fund_id,
                    "split_percentage": item.split_percentage
                }
                new_split = await crud_fund_split.create_fund_split(db=db, fund_split_data=split_data)
                created_splits.append(new_split)
            log.info(f"Created {len(created_splits)} new splits for club {club_id}.")

        await db.flush() # Flush changes
        
        # Eagerly load the fund relationship for each split to prevent lazy loading errors during serialization
        for split in created_splits:
            await db.refresh(split, ["fund"])
            
        log.info(f"Successfully set fund splits for club {club_id}")
        return created_splits

    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        log.exception(f"Unexpected error setting fund splits for club {club_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while setting fund splits."
        )

async def get_fund_splits_for_club(
    db: AsyncSession,
    *,
    club_id: uuid.UUID
) -> Sequence[FundSplit]:
    """ Retrieves all fund splits for a given club. """
    log.debug(f"Retrieving fund splits for club {club_id}")
    splits = await crud_fund_split.get_fund_splits_by_club(db=db, club_id=club_id)
    
    # Eagerly load the fund relationship for each split to prevent lazy loading errors during serialization
    for split in splits:
        await db.refresh(split, ["fund"])
        
    log.debug(f"Found {len(splits)} fund splits for club {club_id}")
    return splits

