# backend/services/fund_service.py

import uuid
import logging
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.crud import fund as crud_fund
from backend.models import Fund
from backend.schemas import FundUpdate

log = logging.getLogger(__name__)

async def update_fund_details(
    db: AsyncSession,
    *,
    fund_id: uuid.UUID,
    fund_in: FundUpdate
) -> Fund:
    """
    Updates details for a specific fund.

    Args:
        db: The AsyncSession instance.
        fund_id: The ID of the fund to update.
        fund_in: The Pydantic schema containing update data.

    Returns:
        The updated Fund model instance.

    Raises:
        HTTPException 404: If the fund is not found.
        HTTPException 500: For unexpected database errors.
    """
    log.info(f"Attempting to update fund {fund_id}")
    # Fetch the fund to update
    db_fund = await crud_fund.get_fund(db=db, fund_id=fund_id)
    if not db_fund:
        log.warning(f"Fund not found for update: {fund_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fund {fund_id} not found")

    # Check if there's any actual data to update
    update_data = fund_in.model_dump(exclude_unset=True)
    if not update_data:
         log.info(f"No update data provided for fund {fund_id}")
         return db_fund # Return original if no changes sent

    try:
        # Pass the original schema object to the CRUD function
        # The CRUD function handles applying the updates
        updated_fund = await crud_fund.update_fund(db=db, db_obj=db_fund, obj_in=fund_in)
        log.info(f"Successfully updated fund {fund_id}")
        return updated_fund
    except Exception as e:
        log.exception(f"Unexpected error updating fund {fund_id}: {e}")
        await db.rollback() # Rollback on error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the fund."
        )

