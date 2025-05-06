# backend/services/accounting_service.py

import uuid
import logging
import os # Added for environment variables
from decimal import Decimal, ROUND_HALF_UP, DivisionByZero
from datetime import date, datetime, timezone # Added timezone
from typing import Dict, Any, Sequence, List, Optional

# Third-party imports
import httpx # Added for async HTTP requests
from dotenv import load_dotenv # Added to load env vars

# Assuming SQLAlchemy and FastAPI are installed in the environment
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlalchemy import select


# Import CRUD functions, Models, Schemas, and other Services
from backend.crud import (
    member_transaction as crud_member_tx,
    unit_value_history as crud_unit_value,
    club_membership as crud_membership,
    club as crud_club,
    fund as crud_fund,
    position as crud_position,
    asset as crud_asset # Added asset CRUD
)
from backend.models import (
    MemberTransaction, UnitValueHistory, ClubMembership, Club, Position, Fund, Asset
)
from backend.models.enums import MemberTransactionType, AssetType # Added AssetType
from backend.schemas import MemberTransactionCreate # Removed unused schema imports


# --- Alpha Vantage Configuration ---
load_dotenv()
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# Configure logging
log = logging.getLogger(__name__)

# Constants
INITIAL_UNIT_VALUE = Decimal("10.00000000")

# --- Market Data Service ---
async def get_market_prices(
    db: AsyncSession, # Add db session to fetch asset details
    asset_ids: Sequence[uuid.UUID],
    valuation_date: date # Keep valuation_date, though AV GlobalQuote gives latest
) -> Dict[uuid.UUID, Decimal]:
    """
    Fetches market prices for given asset IDs using Alpha Vantage GLOBAL_QUOTE.
    Currently only supports STOCK assets. Returns 0 for OPTIONS.
    """
    # ... (Implementation unchanged) ...
    if not ALPHA_VANTAGE_API_KEY:
        log.error("ALPHA_VANTAGE_API_KEY environment variable not set. Cannot fetch market prices.")
        return {asset_id: Decimal("0.0") for asset_id in asset_ids}
    prices: Dict[uuid.UUID, Decimal] = {}
    unique_asset_ids = set(asset_ids)
    asset_details: Dict[uuid.UUID, Asset] = {}
    for asset_id in unique_asset_ids:
        asset = await crud_asset.get_asset(db=db, asset_id=asset_id)
        if asset: asset_details[asset_id] = asset
        else:
            log.warning(f"Asset ID {asset_id} not found in database. Cannot fetch price.")
            prices[asset_id] = Decimal("0.0")
    async with httpx.AsyncClient(timeout=15.0) as client:
        for asset_id, asset in asset_details.items():
            if asset_id in prices: continue
            if asset.asset_type == AssetType.OPTION:
                log.warning(f"Options pricing not supported via Alpha Vantage in MVP. Returning 0 for asset {asset_id} ({asset.symbol}).")
                prices[asset_id] = Decimal("0.0")
                continue
            if asset.asset_type == AssetType.STOCK:
                symbol = asset.symbol
                log.debug(f"Fetching price for STOCK symbol: {symbol} (Asset ID: {asset_id})")
                params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": ALPHA_VANTAGE_API_KEY}
                try:
                    response = await client.get(ALPHA_VANTAGE_BASE_URL, params=params)
                    response.raise_for_status()
                    data = response.json()
                    if "Error Message" in data:
                        log.error(f"Alpha Vantage API error for symbol {symbol}: {data['Error Message']}")
                        prices[asset_id] = Decimal("0.0")
                    elif "Note" in data and "API call frequency" in data["Note"]:
                        log.warning(f"Alpha Vantage rate limit likely hit for symbol {symbol}. Note: {data['Note']}")
                        prices[asset_id] = Decimal("0.0")
                    elif "Global Quote" in data and data["Global Quote"]:
                        quote = data["Global Quote"]
                        price_str = quote.get("05. price")
                        if price_str:
                            try: prices[asset_id] = Decimal(price_str); log.info(f"Successfully fetched price for {symbol}: {prices[asset_id]}")
                            except Exception: log.error(f"Failed to convert price '{price_str}' to Decimal for symbol {symbol}."); prices[asset_id] = Decimal("0.0")
                        else: log.warning(f"Price ('05. price') not found in Alpha Vantage response for symbol {symbol}. Response: {data}"); prices[asset_id] = Decimal("0.0")
                    else:
                        if "Global Quote" in data and not data["Global Quote"]: log.warning(f"Empty 'Global Quote' in Alpha Vantage response for symbol {symbol}. Likely invalid symbol.")
                        else: log.warning(f"Unexpected Alpha Vantage response format for symbol {symbol}. Response: {data}")
                        prices[asset_id] = Decimal("0.0")
                except httpx.HTTPStatusError as e: log.error(f"HTTP error fetching price for {symbol}: {e.response.status_code} - {e.request.url}"); prices[asset_id] = Decimal("0.0")
                except httpx.RequestError as e: log.error(f"Network error fetching price for {symbol}: {e}"); prices[asset_id] = Decimal("0.0")
                except Exception as e: log.exception(f"Unexpected error fetching price for {symbol}: {e}"); prices[asset_id] = Decimal("0.0")
            else: log.warning(f"Asset type '{asset.asset_type}' not supported for price fetching. Asset ID: {asset_id}"); prices[asset_id] = Decimal("0.0")
    log.info(f"Market price fetching complete for valuation date {valuation_date}. Retrieved {len(prices)} prices.")
    for asset_id in asset_ids:
        if asset_id not in prices: prices[asset_id] = Decimal("0.0"); log.warning(f"Asset ID {asset_id} was requested but not found in results, defaulting price to 0.0.")
    return prices


# --- Member Deposit/Withdrawal Processing ---
async def process_member_deposit(
    db: AsyncSession,
    *,
    deposit_in: MemberTransactionCreate,
) -> MemberTransaction:
    """ Processes a member deposit. """
    if deposit_in.transaction_type != MemberTransactionType.DEPOSIT: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Transaction type must be Deposit.")
    if deposit_in.amount <= Decimal("0"): raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deposit amount must be positive.")
    log.info(f"Processing deposit for user {deposit_in.user_id} in club {deposit_in.club_id} amount {deposit_in.amount}")
    membership = await crud_membership.get_club_membership_by_user_and_club(db=db, user_id=deposit_in.user_id, club_id=deposit_in.club_id)
    if not membership: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User membership in the specified club not found.")
    club = await crud_club.get_club(db=db, club_id=deposit_in.club_id)
    if not club: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Club {deposit_in.club_id} not found.")
    latest_unit_record = await crud_unit_value.get_latest_unit_value_for_club(db=db, club_id=club.id)
    unit_value_used: Decimal
    if latest_unit_record: unit_value_used = latest_unit_record.unit_value; log.info(f"Using latest unit value for club {club.id}: {unit_value_used}")
    else: unit_value_used = INITIAL_UNIT_VALUE; log.info(f"No unit value history found for club {club.id}. Using initial unit value: {unit_value_used}")
    if unit_value_used <= Decimal("0"): log.error(f"Unit value is zero or negative ({unit_value_used}) for club {club.id}. Cannot calculate units."); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot process deposit: Invalid unit value.")
    try: units_transacted = (deposit_in.amount / unit_value_used).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP); log.info(f"Calculated units for deposit: {units_transacted}")
    except DivisionByZero: log.error(f"Division by zero error calculating units for club {club.id} with unit value {unit_value_used}."); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error calculating units for deposit.")
    member_tx_data = {"membership_id": membership.id, "transaction_type": MemberTransactionType.DEPOSIT, "amount": deposit_in.amount, "transaction_date": deposit_in.transaction_date, "unit_value_used": unit_value_used, "units_transacted": units_transacted, "notes": deposit_in.notes}
    try:
        created_member_tx = await crud_member_tx.create_member_transaction(db=db, member_tx_data=member_tx_data)
        log.info(f"Created member transaction {created_member_tx.id}")
        club.bank_account_balance += deposit_in.amount
        db.add(club) # Add the actual club object
        log.info(f"Updated club {club.id} bank balance to {club.bank_account_balance}")
        await db.flush() # Flush the real session
        log.info(f"Successfully processed member deposit {created_member_tx.id}")
        # --- FIX: Removed problematic refresh calls ---
        # await db.refresh(created_member_tx)
        # await db.refresh(club)
        # --- END FIX ---
        return created_member_tx # Return the object as created/refreshed by CRUD
    except IntegrityError as e: log.exception(f"Database integrity error processing deposit for user {deposit_in.user_id}, club {deposit_in.club_id}: {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Database conflict processing deposit: {e}")
    except HTTPException as e: await db.rollback(); raise e
    except Exception as e: log.exception(f"Unexpected error processing deposit for user {deposit_in.user_id}, club {deposit_in.club_id}: {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred processing the deposit.")


async def process_member_withdrawal(
    db: AsyncSession,
    *,
    withdrawal_in: MemberTransactionCreate,
) -> MemberTransaction:
    """ Processes a member withdrawal. """
    if withdrawal_in.transaction_type != MemberTransactionType.WITHDRAWAL: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Transaction type must be Withdrawal.")
    if withdrawal_in.amount <= Decimal("0"): raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Withdrawal amount must be positive.")
    log.info(f"Processing withdrawal for user {withdrawal_in.user_id} in club {withdrawal_in.club_id} amount {withdrawal_in.amount}")
    membership = await crud_membership.get_club_membership_by_user_and_club(db=db, user_id=withdrawal_in.user_id, club_id=withdrawal_in.club_id)
    if not membership: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User membership in the specified club not found.")
    club = await crud_club.get_club(db=db, club_id=withdrawal_in.club_id)
    if not club: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Club {withdrawal_in.club_id} not found.")
    latest_unit_record = await crud_unit_value.get_latest_unit_value_for_club(db=db, club_id=club.id)
    if not latest_unit_record: log.error(f"No unit value history found for club {club.id}. Cannot process withdrawal."); raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cannot process withdrawal: No unit value history found for club.")
    unit_value_used = latest_unit_record.unit_value
    log.info(f"Using latest unit value for withdrawal: {unit_value_used}")
    if unit_value_used <= Decimal("0"): log.error(f"Unit value is zero or negative ({unit_value_used}) for club {club.id}. Cannot calculate units for withdrawal."); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cannot process withdrawal: Invalid unit value.")
    try: units_being_redeemed = (withdrawal_in.amount / unit_value_used).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP); log.info(f"Calculated units to redeem for withdrawal: {units_being_redeemed}")
    except DivisionByZero: log.error(f"Division by zero error calculating units for withdrawal in club {club.id}."); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error calculating units for withdrawal.")
    try: current_member_units = await crud_member_tx.get_member_unit_balance(db=db, membership_id=membership.id); log.info(f"Member {membership.id} current unit balance: {current_member_units}")
    except Exception as e: log.exception(f"Error retrieving unit balance for membership {membership.id}: {e}"); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve member unit balance.")
    if current_member_units < units_being_redeemed: log.warning(f"Insufficient units for withdrawal for membership {membership.id}. Required: {units_being_redeemed}, Available: {current_member_units}"); raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Insufficient units for withdrawal. Required: {units_being_redeemed:.8f}, Available: {current_member_units:.8f}")
    if club.bank_account_balance < withdrawal_in.amount: log.warning(f"Insufficient cash in club bank account {club.id} for withdrawal. Required: {withdrawal_in.amount}, Available: {club.bank_account_balance}"); raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Insufficient cash in club bank account to cover withdrawal. Required: {withdrawal_in.amount:.2f}, Available: {club.bank_account_balance:.2f}")
    member_tx_data = {"membership_id": membership.id, "transaction_type": MemberTransactionType.WITHDRAWAL, "amount": withdrawal_in.amount, "transaction_date": withdrawal_in.transaction_date, "unit_value_used": unit_value_used, "units_transacted": -units_being_redeemed, "notes": withdrawal_in.notes}
    try:
        created_member_tx = await crud_member_tx.create_member_transaction(db=db, member_tx_data=member_tx_data)
        log.info(f"Created member transaction {created_member_tx.id} for withdrawal.")
        club.bank_account_balance -= withdrawal_in.amount
        db.add(club) # Add the actual club object
        log.info(f"Updated club {club.id} bank balance to {club.bank_account_balance}")
        await db.flush() # Flush the real session
        log.info(f"Successfully processed member withdrawal {created_member_tx.id}")
        # --- FIX: Removed problematic refresh calls ---
        # await db.refresh(created_member_tx)
        # await db.refresh(club)
        # --- END FIX ---
        return created_member_tx # Return object as created/refreshed by CRUD
    except IntegrityError as e: log.exception(f"Database integrity error processing withdrawal for user {withdrawal_in.user_id}, club {withdrawal_in.club_id}: {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Database conflict processing withdrawal: {e}")
    except HTTPException as e: await db.rollback(); raise e
    except Exception as e: log.exception(f"Unexpected error processing withdrawal for user {withdrawal_in.user_id}, club {withdrawal_in.club_id}: {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred processing the withdrawal.")


# --- NAV Calculation ---
async def calculate_and_store_nav(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    valuation_date: date
) -> UnitValueHistory:
    """
    Calculates the Net Asset Value (NAV) and NAV per unit for a club on a specific date
    and stores it in the UnitValueHistory table.
    """
    log.info(f"Calculating NAV for club {club_id} on {valuation_date}")

    # 1. Fetch Club with related Funds, Positions, and Assets
    stmt = (
        select(Club)
        .where(Club.id == club_id)
        .options(
            selectinload(Club.funds)
            .selectinload(Fund.positions)
            .selectinload(Position.asset)
        )
    )
    result = await db.execute(stmt)
    club = result.unique().scalar_one_or_none()

    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Club {club_id} not found.")

    # 2. Aggregate Positions and Identify Unique Assets
    all_positions: list[Position] = []
    all_asset_ids: set[uuid.UUID] = set()
    total_brokerage_cash = Decimal("0.0")
    funds = club.funds
    for fund in funds:
        total_brokerage_cash += fund.brokerage_cash_balance
        fund_positions = fund.positions
        all_positions.extend(fund_positions)
        for pos in fund_positions:
            if pos.asset and pos.asset.id:
                 all_asset_ids.add(pos.asset.id)
            else:
                 log.warning(f"Position {pos.id} in fund {fund.id} is missing asset information.")

    # 3. Fetch Market Prices using the integrated service
    try:
        market_prices = await get_market_prices(db, list(all_asset_ids), valuation_date) # Pass db session
    except Exception as e:
        log.exception(f"Failed to fetch market prices for club {club_id} on {valuation_date}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to retrieve market prices for NAV calculation: {e}"
        )

    # 4. Calculate Total Market Value of Positions
    total_market_value = Decimal("0.0")
    for pos in all_positions:
        price = market_prices.get(pos.asset_id, Decimal("0.0"))
        if price == Decimal("0.0") and pos.asset_id in all_asset_ids:
             log.warning(f"Using price 0.0 for asset {pos.asset_id} (Symbol: {pos.asset.symbol if pos.asset else 'N/A'}) in NAV calculation.")
        total_market_value += pos.quantity * price
        log.debug(f"Position {pos.id} (Asset: {pos.asset.symbol if pos.asset else 'N/A'}, Qty: {pos.quantity}) value: {(pos.quantity * price):.2f} (Price: {price})")

    log.info(f"Total market value of positions for club {club_id}: {total_market_value:.2f}")

    # 5. Calculate Total Cash
    total_cash = club.bank_account_balance + total_brokerage_cash
    log.info(f"Total cash for club {club_id}: {total_cash:.2f} (Bank: {club.bank_account_balance}, Brokerage: {total_brokerage_cash})")

    # 6. Calculate Total Club Value (NAV)
    total_club_value = total_market_value + total_cash
    log.info(f"Total club value (NAV) for club {club_id}: {total_club_value:.2f}")

    # 7. Get Total Units Outstanding
    try:
        total_units_outstanding = await crud_member_tx.get_total_units_for_club(db=db, club_id=club.id)
        log.info(f"Total units outstanding for club {club.id}: {total_units_outstanding}")
    except Exception as e:
        log.exception(f"Error retrieving total units for club {club.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve total club units.")

    # 8. Calculate NAV per Unit
    unit_value = Decimal("0.0")
    if total_units_outstanding > Decimal("0"):
        try:
            unit_value = (total_club_value / total_units_outstanding).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)
            log.info(f"Calculated NAV per unit for club {club.id}: {unit_value}")
        except DivisionByZero:
            log.error(f"Division by zero calculating unit value for club {club.id} (Total Value: {total_club_value}, Total Units: {total_units_outstanding})");
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error calculating NAV per unit (division by zero).")
    elif total_club_value != Decimal("0.0"):
        log.warning(f"Club {club.id} has value ({total_club_value}) but zero units outstanding. Setting unit value to 0.")
        unit_value = Decimal("0.0")
    else:
        log.info(f"Club {club.id} has zero value and zero units. Setting unit value to 0.")
        unit_value = Decimal("0.0")

    # 9. Store Unit Value History
    history_data = {
        "club_id": club.id,
        "valuation_date": valuation_date,
        "total_club_value": total_club_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        "total_units_outstanding": total_units_outstanding,
        "unit_value": unit_value
    }
    try:
        new_history_record = await crud_unit_value.create_unit_value_history(db=db, uvh_data=history_data)
        log.info(f"Stored unit value history for club {club.id} on {valuation_date} (ID: {new_history_record.id})")
        # --- FIX: Removed problematic refresh call ---
        # await db.refresh(new_history_record, attribute_names=['club'])
        # --- END FIX ---
        return new_history_record # Return object as created/refreshed by CRUD
    except IntegrityError as e:
        log.warning(f"IntegrityError storing unit value history for club {club_id} on {valuation_date}. It might already exist. Error: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Unit value history for club {club_id} on {valuation_date} already exists.")
    except Exception as e:
        log.exception(f"Unexpected error storing unit value history for club {club_id} on {valuation_date}: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while storing unit value history.")


# --- Member Equity Calculation ---
async def get_member_equity(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    user_id: uuid.UUID
) -> Decimal:
    """
    Calculates the current equity (value) of a specific member in a club.
    (Implementation unchanged)
    """
    log.info(f"Calculating equity for user {user_id} in club {club_id}")
    membership = await crud_membership.get_club_membership_by_user_and_club(db=db, user_id=user_id, club_id=club_id)
    if not membership: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Membership for user {user_id} in club {club_id} not found.")
    try: member_units = await crud_member_tx.get_member_unit_balance(db=db, membership_id=membership.id)
    except Exception as e: log.exception(f"Error retrieving unit balance for membership {membership.id}: {e}"); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve member unit balance.")
    if member_units <= Decimal("0"): log.info(f"Member {user_id} has zero or negative units ({member_units}) in club {club_id}. Equity is 0."); return Decimal("0.00")
    latest_unit_record = await crud_unit_value.get_latest_unit_value_for_club(db=db, club_id=club_id)
    if not latest_unit_record: log.warning(f"No unit value history found for club {club_id}. Cannot calculate member equity accurately. Returning 0."); return Decimal("0.00")
    latest_unit_value = latest_unit_record.unit_value
    log.debug(f"Club {club_id} latest unit value: {latest_unit_value}")
    if latest_unit_value < Decimal("0"): log.error(f"Latest unit value for club {club_id} is negative ({latest_unit_value}). Equity calculation may be incorrect."); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Club unit value is negative, cannot calculate equity.")
    member_equity = (member_units * latest_unit_value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    log.info(f"Calculated equity for user {user_id} in club {club_id}: {member_equity:.2f}")
    return member_equity
