# backend/services/fund_service.py

import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError  # For handling potential unique constraint violations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from backend.crud import fund as crud_fund
from backend.crud import position as crud_position
from backend.crud import unit_value_history as crud_unit_value
from backend.schemas import FundCreate  # Add this for the new function
from backend.models import Fund, Position, UnitValueHistory, Club
from backend.schemas import FundUpdate, FundReadDetailed, FundPerformanceHistoryPoint, FundPerformanceHistoryResponse

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

async def get_fund_detailed(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    fund_id: uuid.UUID
) -> FundReadDetailed:
    """
    Retrieves detailed information about a fund including calculated metrics.

    Args:
        db: The AsyncSession instance.
        club_id: The ID of the club the fund belongs to.
        fund_id: The ID of the fund to retrieve.

    Returns:
        FundReadDetailed schema with fund details and calculated metrics.

    Raises:
        HTTPException 404: If the fund is not found.
        HTTPException 500: For unexpected database errors.
    """
    log.info(f"Retrieving detailed information for fund {fund_id} in club {club_id}")
    
    # Fetch the fund with related data
    stmt = (
        select(Fund)
        .where(Fund.id == fund_id, Fund.club_id == club_id)
        .options(
            selectinload(Fund.positions).selectinload(Position.asset),
            selectinload(Fund.club)
        )
    )
    
    result = await db.execute(stmt)
    fund = result.unique().scalar_one_or_none()
    
    if not fund:
        log.warning(f"Fund {fund_id} not found in club {club_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fund {fund_id} not found in club {club_id}"
        )
    
    try:
        # Calculate positions market value
        positions_market_value = Decimal("0.0")
        for position in fund.positions:
            # In a real implementation, we would use current market prices
            # For now, we'll use the average price as a placeholder
            current_price = position.average_price  # This should be replaced with actual market price
            positions_market_value += position.quantity * current_price
        
        # Get cash balance from the fund
        cash_balance = fund.brokerage_cash_balance
        
        # Calculate total fund value
        total_value = cash_balance + positions_market_value
        
        # Calculate percentage of club assets
        # First, get total club value
        club_total_value = Decimal("0.0")
        club_funds_stmt = select(Fund).where(Fund.club_id == club_id)
        result = await db.execute(club_funds_stmt)
        club_funds = result.scalars().all()
        
        for club_fund in club_funds:
            # Add cash balance
            club_total_value += club_fund.brokerage_cash_balance
            
            # Add positions value if it's not the current fund
            if club_fund.id != fund_id:
                fund_positions_stmt = select(Position).where(Position.fund_id == club_fund.id)
                result = await db.execute(fund_positions_stmt)
                fund_positions = result.scalars().all()
                
                for position in fund_positions:
                    # Again, using average price as placeholder for current price
                    club_total_value += position.quantity * position.average_price
        
        # Add the current fund's positions value we calculated earlier
        club_total_value += positions_market_value
        
        # Calculate percentage (avoid division by zero)
        percentage_of_club_assets = Decimal("0.0")
        if club_total_value > Decimal("0.0"):
            percentage_of_club_assets = (total_value / club_total_value) * Decimal("100.0")
        
        # Create the detailed fund response
        fund_detailed = FundReadDetailed(
            id=fund.id,
            club_id=fund.club_id,
            name=fund.name,
            description=fund.description,
            is_active=fund.is_active,
            brokerage_cash_balance=fund.brokerage_cash_balance,
            created_at=fund.created_at,
            updated_at=fund.updated_at,
            club=fund.club,
            cash_balance=cash_balance,
            positions_market_value=positions_market_value,
            total_value=total_value,
            percentage_of_club_assets=percentage_of_club_assets
        )
        
        log.info(f"Successfully retrieved detailed information for fund {fund_id}")
        return fund_detailed
        
    except Exception as e:
        log.exception(f"Unexpected error retrieving detailed information for fund {fund_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving fund details."
        )

async def get_fund_performance_history(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    fund_id: uuid.UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> FundPerformanceHistoryResponse:
    """
    Retrieves historical performance data for a specific fund.

    Args:
        db: The AsyncSession instance.
        club_id: The ID of the club the fund belongs to.
        fund_id: The ID of the fund to retrieve history for.
        start_date: Optional start date for filtering history.
        end_date: Optional end date for filtering history.

    Returns:
        FundPerformanceHistoryResponse containing historical data points.

    Raises:
        HTTPException 404: If the fund is not found.
        HTTPException 500: For unexpected database errors.
    """
    log.info(f"Retrieving performance history for fund {fund_id} in club {club_id}")
    
    # Verify the fund exists and belongs to the club
    fund = await crud_fund.get_fund(db=db, fund_id=fund_id)
    if not fund or fund.club_id != club_id:
        log.warning(f"Fund {fund_id} not found in club {club_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fund {fund_id} not found in club {club_id}"
        )
    
    try:
        # Set default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            # Default to 3 months of history
            start_date = end_date - timedelta(days=90)
        
        # In a real implementation, we would query historical fund values from a table
        # For now, we'll generate some sample data points
        # This should be replaced with actual database queries
        
        # Generate sample data points (one per week)
        history_points: List[FundPerformanceHistoryPoint] = []
        current_date = start_date
        base_value = Decimal("10000.00")  # Starting value
        growth_factor = Decimal("1.005")  # Small growth per data point
        
        while current_date <= end_date:
            # Create a data point
            history_points.append(
                FundPerformanceHistoryPoint(
                    valuation_date=current_date,
                    total_value=base_value
                )
            )
            
            # Move to next week and increase value slightly
            current_date += timedelta(days=7)
            base_value *= growth_factor
        
        response = FundPerformanceHistoryResponse(history=history_points)
        log.info(f"Successfully retrieved {len(history_points)} performance history points for fund {fund_id}")
        return response
        
    except Exception as e:
        log.exception(f"Unexpected error retrieving performance history for fund {fund_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving fund performance history."
        )


async def create_new_fund_for_club(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    fund_in: FundCreate  # Use the FundCreate schema for input
) -> Fund:
    """
    Creates a new fund for a specific club.

    Args:
        db: The AsyncSession instance.
        club_id: The ID of the club to create the fund for.
        fund_in: Pydantic schema containing the new fund's data (name, description).

    Returns:
        The newly created Fund model instance.

    Raises:
        HTTPException 404: If the parent club is not found (optional check, could be handled by FK constraint).
        HTTPException 409: If a fund with the same name already exists in the club.
        HTTPException 500: For unexpected database errors.
    """
    log.info(f"Attempting to create new fund '{fund_in.name}' for club {club_id}")

    # Optional: Check if club exists (though FK constraint on Fund.club_id should handle this)
    # parent_club = await crud_club.get_club(db=db, club_id=club_id) # Assuming crud_club is available
    # if not parent_club:
    #     log.warning(f"Club {club_id} not found for creating new fund.")
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Club {club_id} not found.")

    # Check if a fund with the same name already exists for this club
    existing_fund = await crud_fund.get_fund_by_club_and_name(db=db, club_id=club_id, name=fund_in.name)
    if existing_fund:
        log.warning(f"Fund with name '{fund_in.name}' already exists for club {club_id}.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A fund with the name '{fund_in.name}' already exists in this club."
        )

    fund_data_dict = {
        "club_id": club_id,
        "name": fund_in.name,
        "description": fund_in.description,
        "is_active": True,  # New funds are active by default
        "brokerage_cash_balance": Decimal("0.00") # New funds start with zero cash
    }

    try:
        new_fund = await crud_fund.create_fund(db=db, fund_data=fund_data_dict)
        await db.flush() # Ensure data is written before returning
        await db.refresh(new_fund) # Ensure the returned object has all DB-generated fields
        log.info(f"Successfully created new fund {new_fund.id} ('{new_fund.name}') for club {club_id}")
        return new_fund
    except IntegrityError as e: # Catch more specific errors if possible
        log.exception(f"Database integrity error creating fund '{fund_in.name}' for club {club_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Failed to create fund due to a data conflict (e.g., unique constraint).")
    except Exception as e:
        log.exception(f"Unexpected error creating fund '{fund_in.name}' for club {club_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the fund."
        )
