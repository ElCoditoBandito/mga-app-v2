# backend/services/reporting_service.py

import uuid
import logging
from decimal import Decimal, ROUND_HALF_UP, DivisionByZero
from datetime import date, datetime, timedelta
from typing import Dict, Any, Sequence, List, Optional

# Direct imports - Ensure these are installed in your environment
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlalchemy import select

# Import CRUD functions, Models, Schemas, and other Services
from backend.crud import (
    club as crud_club,
    unit_value_history as crud_unit_value,
    member_transaction as crud_member_tx,
    club_membership as crud_membership,
)
from backend.models import (
    Club, Position, Fund, Asset, UnitValueHistory, MemberTransaction, ClubMembership
)
# Import necessary schemas, including the moved reporting schemas
from backend.schemas import (
    ClubPortfolio, PositionRead, UnitValueHistoryRead, MemberTransactionRead,
    MemberStatementData, ClubPerformanceData # Import the moved schemas
)
from backend.services.accounting_service import get_market_prices, get_member_equity

# Configure logging for this module
log = logging.getLogger(__name__)

# --- Service Functions ---

async def get_club_portfolio_report(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    valuation_date: date = date.today()
) -> ClubPortfolio:
    """
    Generates a portfolio report for a club on a specific valuation date.
    """
    log.info(f"Generating portfolio report for club {club_id} on {valuation_date}")

    # 1. Fetch Club with related Funds, Positions, and Assets eagerly loaded
    stmt = (
        select(Club)
        .where(Club.id == club_id)
        .options(
            selectinload(Club.funds) # Load funds related to the club
            .selectinload(Fund.positions) # Load positions related to each fund
            .selectinload(Position.asset) # Load the asset related to each position
        )
    )
    result = await db.execute(stmt)
    club = result.unique().scalar_one_or_none()

    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Club {club_id} not found.")

    # 2. Aggregate Positions and Identify Unique Assets
    all_positions_models: list[Position] = []
    all_asset_ids: set[uuid.UUID] = set()
    total_brokerage_cash = Decimal("0.0")

    for fund in club.funds:
        total_brokerage_cash += fund.brokerage_cash_balance
        for pos in fund.positions:
            all_positions_models.append(pos)
            # Ensure asset and asset.id are not None before adding
            if pos.asset and pos.asset.id:
                all_asset_ids.add(pos.asset.id)
            else:
                # Log a warning if a position is missing asset info (shouldn't happen with eager loading if data is consistent)
                log.warning(f"Position {pos.id} in fund {fund.id} is missing asset information after eager load attempt.")

    # 3. Fetch Market Prices using the integrated service
    try:
        market_prices = await get_market_prices(db, list(all_asset_ids), valuation_date)
    except Exception as e:
        log.exception(f"Failed to fetch market prices for club {club_id} report on {valuation_date}: {e}")
        # Consider specific error handling for market data failures if needed
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve market prices for report.")

    # 4. Calculate Total Market Value of Positions and prepare PositionRead objects
    total_market_value = Decimal("0.0")
    aggregated_positions_read: list[PositionRead] = []

    for pos_model in all_positions_models:
        position_market_value = Decimal("0.0")
        price = Decimal("0.0") # Default price if not found

        # Check if asset exists and price was found
        if pos_model.asset and pos_model.asset.id in market_prices:
            price = market_prices[pos_model.asset.id]
            position_market_value = pos_model.quantity * price
            total_market_value += position_market_value
        elif pos_model.asset:
            # Log if price wasn't found for a known asset
            log.warning(f"Market price not found for asset {pos_model.asset.id} ({pos_model.asset.symbol}) on {valuation_date}. Value will be 0.")

        # Validate the Position model against the PositionRead schema
        try:
            # Ensure relationships needed by PositionRead (asset, fund) are loaded
            # The initial query with selectinload should handle this
            pos_read = PositionRead.model_validate(pos_model)
            aggregated_positions_read.append(pos_read)
        except Exception as e:
            # Log error if validation fails for a specific position
            asset_symbol = pos_model.asset.symbol if pos_model.asset else 'N/A'
            log.error(f"Error validating Position model {pos_model.id} (Asset: {asset_symbol}) to schema: {e}. Skipping position in report.")

    # 5. Calculate Total Cash Value
    total_cash_value = club.bank_account_balance + total_brokerage_cash

    # 6. Get Latest Unit Value History Record
    latest_unit_record_model = await crud_unit_value.get_latest_unit_value_for_club(
        db=db, club_id=club.id
    )
    latest_unit_record_read: Optional[UnitValueHistoryRead] = None
    if latest_unit_record_model:
        try:
            # Validate the history model against the UnitValueHistoryRead schema
            latest_unit_record_read = UnitValueHistoryRead.model_validate(latest_unit_record_model)
        except Exception as e:
            log.error(f"Error validating UnitValueHistory model {latest_unit_record_model.id} to schema: {e}")

    # 7. Construct the Final Report Object
    # Ensure values are quantized for consistent decimal places
    report_data = ClubPortfolio(
        club_id=club.id,
        valuation_date=valuation_date,
        total_market_value=total_market_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        total_cash_value=total_cash_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        aggregated_positions=aggregated_positions_read,
        recent_unit_value=latest_unit_record_read
    )

    log.info(f"Successfully generated portfolio report for club {club_id} on {valuation_date}")
    return report_data


async def get_member_statement(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    user_id: uuid.UUID
) -> MemberStatementData:
    """
    Generates a statement for a specific member within a club.
    """
    log.info(f"Generating statement for user {user_id} in club {club_id}")

    # 1. Get Membership
    membership = await crud_membership.get_club_membership_by_user_and_club(
        db=db, user_id=user_id, club_id=club_id
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Membership for user {user_id} in club {club_id} not found.")

    # 2. Get Member Transactions
    # Use limit=0 to fetch all transactions for the statement
    member_tx_models = await crud_member_tx.get_multi_member_transactions(
        db=db, membership_id=membership.id, limit=0
    )

    # Validate transactions against the read schema
    member_tx_reads: list[MemberTransactionRead] = []
    for tx_model in member_tx_models:
        try:
            # Ensure relationships needed by schema (user, club via membership) are loaded
            # crud_member_tx.get_multi_member_transactions should handle this
            member_tx_reads.append(MemberTransactionRead.model_validate(tx_model))
        except Exception as e:
            log.error(f"Error validating MemberTransaction model {tx_model.id} to schema: {e}")

    # 3. Get Current Unit Balance
    try:
        current_unit_balance = await crud_member_tx.get_member_unit_balance(
            db=db, membership_id=membership.id
        )
    except Exception as e:
        log.exception(f"Error retrieving unit balance for membership {membership.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve member unit balance.")

    # 4. Get Latest Unit Value and Calculate Equity
    latest_unit_value: Optional[Decimal] = None
    current_equity: Decimal = Decimal("0.00")

    latest_unit_record = await crud_unit_value.get_latest_unit_value_for_club(
        db=db, club_id=club_id
    )

    if latest_unit_record:
        latest_unit_value = latest_unit_record.unit_value
        # Ensure unit value is valid before calculating equity
        if latest_unit_value is not None and latest_unit_value >= Decimal("0"):
            current_equity = (current_unit_balance * latest_unit_value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            log.warning(f"Latest unit value for club {club_id} is missing or negative ({latest_unit_value}). Setting equity to 0 for statement.")
    else:
        log.warning(f"No unit value history found for club {club_id}. Cannot calculate current equity.")

    # 5. Construct Statement Data
    statement_data = MemberStatementData(
        club_id=club_id,
        user_id=user_id,
        membership_id=membership.id,
        statement_date=date.today(), # Or consider passing a specific statement date
        current_unit_balance=current_unit_balance,
        latest_unit_value=latest_unit_value,
        current_equity_value=current_equity,
        transactions=member_tx_reads
    )

    log.info(f"Successfully generated statement for user {user_id} in club {club_id}")
    return statement_data


async def get_club_performance(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    start_date: date,
    end_date: date
) -> ClubPerformanceData:
    """
    Calculates the simple Holding Period Return (HPR) for a club based on unit values.
    """
    log.info(f"Calculating performance for club {club_id} from {start_date} to {end_date}")

    if start_date > end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date cannot be after end date.")

    # 1. Fetch Unit Value History for the period
    try:
        # Ensure the CRUD function exists and handles the date range correctly
        history = await crud_unit_value.get_unit_value_history_for_period(
            db=db, club_id=club_id, start_date=start_date, end_date=end_date
        )
    except AttributeError:
        # Catch if the CRUD function is missing
        log.error("CRUD function 'get_unit_value_history_for_period' not found.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error: Cannot retrieve unit value history.")
    except Exception as e:
        log.exception(f"Error fetching unit value history for club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve unit value history.")

    # 2. Determine Start and End Values
    start_value: Optional[Decimal] = None
    end_value: Optional[Decimal] = None
    hpr: Optional[float] = None

    if history:
        # Ensure history is sorted by date (CRUD function should handle this)
        # history.sort(key=lambda h: h.valuation_date) # Usually not needed if CRUD orders
        start_record = history[0] # First record in the period
        end_record = history[-1] # Last record in the period

        start_value = start_record.unit_value
        end_value = end_record.unit_value
        log.info(f"Found start value {start_value} on {start_record.valuation_date} and end value {end_value} on {end_record.valuation_date}")

        # 3. Calculate HPR
        if start_value is not None and start_value > Decimal("0") and end_value is not None:
            try:
                hpr_decimal = (end_value / start_value) - Decimal("1.0")
                hpr = float(hpr_decimal) # Convert to float for the response schema
                log.info(f"Calculated HPR: {hpr:.4f}")
            except DivisionByZero:
                log.warning(f"Cannot calculate HPR for club {club_id} due to zero start value.")
                hpr = None
            except Exception as e:
                log.exception(f"Error calculating HPR for club {club_id}: {e}")
                hpr = None
        else:
            log.warning(f"Could not calculate HPR for club {club_id}: Start value ({start_value}) or end value ({end_value}) is missing or invalid.")
    else:
        log.warning(f"No unit value history found for club {club_id} between {start_date} and {end_date}.")

    # 4. Construct Performance Data Object
    performance_data = ClubPerformanceData(
        club_id=club_id,
        start_date=start_date,
        end_date=end_date,
        start_unit_value=start_value,
        end_unit_value=end_value,
        holding_period_return=hpr
    )

    return performance_data
