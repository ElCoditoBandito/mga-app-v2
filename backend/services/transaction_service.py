# backend/services/transaction_service.py

import uuid
import logging # Import logging
from decimal import Decimal, ROUND_HALF_UP, DivisionByZero
from typing import Dict, Any, Tuple, Sequence, Union # Added Union
from datetime import datetime

# Assuming SQLAlchemy and FastAPI are installed in the environment
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

# Import CRUD functions, Models, Schemas, and Enums
from backend.crud import (
    transaction as crud_transaction,
    position as crud_position,
    fund as crud_fund,
    asset as crud_asset,
    club as crud_club,
    fund_split as crud_fund_split,
)
# Added Club model and FundSplit model
from backend.models import Transaction, Position, Fund, Asset, Club, FundSplit # [cite: backend_files/models/transaction.py, backend_files/models/position.py, backend_files/models/fund.py, backend_files/models/asset.py, backend_files/models/club.py, backend_files/models/fund_split.py]
# Import specific transaction types and OptionType
from backend.models.enums import TransactionType, OptionType # [cite: backend_files/models/enums.py]
# Import specific schemas
from backend.schemas import ( # Added TransactionCreateCashTransfer, TransactionCreateOptionLifecycle
    TransactionCreateTrade,
    TransactionCreateDividendBrokerageInterest,
    TransactionCreateCashTransfer,
    TransactionCreateOptionLifecycle,
    TransactionCreateClubExpense,
) # [cite: backend_files/schemas/transaction.py]

# Configure logging for this module
log = logging.getLogger(__name__)

# Define trade types for easier checking
BUY_TYPES = {
    TransactionType.BUY_STOCK,
    TransactionType.BUY_OPTION, # BuyToOpen
    TransactionType.CLOSE_OPTION_BUY, # BuyToClose
}
SELL_TYPES = {
    TransactionType.SELL_STOCK,
    TransactionType.SELL_OPTION, # SellToOpen
    TransactionType.CLOSE_OPTION_SELL, # SellToClose
}

# --- Helper Function for Position Updates (Internal Use) ---
async def _update_or_create_position(
    db: AsyncSession,
    *,
    fund_id: uuid.UUID,
    asset_id: uuid.UUID,
    quantity_change: Decimal, # Positive for buy/increase, negative for sell/decrease
    price_per_unit: Decimal, # Price for calculating cost basis on buys
) -> Position:
    """
    Internal helper to get, update, or create a position based on a transaction.
    Calculates average cost basis only when quantity increases (buys).

    Args:
        db: AsyncSession instance.
        fund_id: ID of the fund.
        asset_id: ID of the asset.
        quantity_change: The change in quantity (+ for buy, - for sell).
        price_per_unit: The price per unit of the transaction (used for cost basis on buys).

    Returns:
        The updated or newly created Position object.

    Raises:
        HTTPException 400: If attempting to reduce quantity below zero.
        HTTPException 500: If creating a position fails unexpectedly.
    """
    position = await crud_position.get_position_by_fund_and_asset(db=db, fund_id=fund_id, asset_id=asset_id) # [cite: backend_files/crud/position.py]

    if position:
        log.debug(f"Updating existing position {position.id} for fund {fund_id}, asset {asset_id}. Change: {quantity_change}")
        old_qty = position.quantity
        new_qty = old_qty + quantity_change

        if new_qty < Decimal("0"):
            # This check prevents selling more than owned, including short positions going further negative than intended.
            # Specific handling for short covering vs opening new shorts might need more complex logic if required.
            log.warning(f"Attempt to reduce position quantity below zero for position {position.id}. Current: {old_qty}, Change: {quantity_change}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction quantity exceeds available position quantity.")

        position.quantity = new_qty

        # Update average cost basis only on buys (increase in quantity)
        if quantity_change > Decimal("0"):
            old_avg_cost = position.average_cost_basis
            if new_qty != Decimal("0"): # Avoid division by zero
                # Ensure price is Decimal
                if isinstance(price_per_unit, Decimal):
                    new_avg_cost = ((old_avg_cost * old_qty) + (price_per_unit * quantity_change)) / new_qty
                    position.average_cost_basis = new_avg_cost
                    log.debug(f"Position {position.id} cost basis updated to {new_avg_cost}")
                else:
                    log.error(f"Invalid price type '{type(price_per_unit)}' for cost basis calculation on position {position.id}.")
                    # Decide handling: raise error or log and skip update? For now, log and skip.
            else: # Should not happen if quantity_change > 0, but defensive
                position.average_cost_basis = Decimal("0.0")

        db.add(position) # Add updated position to session
        return position
    else:
        # Position doesn't exist, create it (only if quantity_change is positive)
        if quantity_change > Decimal("0"):
            log.debug(f"Creating new position for fund {fund_id}, asset {asset_id}. Quantity: {quantity_change}")
            position_data = {
                "fund_id": fund_id,
                "asset_id": asset_id,
                "quantity": quantity_change,
                "average_cost_basis": price_per_unit if isinstance(price_per_unit, Decimal) else Decimal("0.0")
            }
            try:
                new_position = await crud_position.create_position(db=db, position_data=position_data) # [cite: backend_files/crud/position.py]
                return new_position
            except Exception as e:
                log.exception(f"Failed to create position for fund {fund_id}, asset {asset_id}: {e}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create position record.")
        else:
            # Cannot create a position with a negative initial quantity change (e.g., first transaction is a sell)
            log.error(f"Attempted to create position with non-positive quantity change ({quantity_change}) for fund {fund_id}, asset {asset_id}.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot initiate a position with a sell or zero quantity transaction.")


async def process_trade_transaction(
    db: AsyncSession,
    *,
    trade_in: TransactionCreateTrade,
) -> Transaction:
    """
    Processes a trade transaction (buy/sell stock/option), creates the transaction record,
    updates the corresponding position, and adjusts the fund's cash balance.
    """
    # --- DEBUGGING ---
    log.debug(f"DEBUG: process_trade_transaction received trade_in of type: {type(trade_in)}")
    log.debug(f"DEBUG: trade_in content: {trade_in}")
    try:
        log.debug(f"DEBUG: trade_in.fund_id: {getattr(trade_in, 'fund_id', 'NOT FOUND')}")
    except Exception as e:
        log.error(f"DEBUG: Error accessing trade_in.fund_id: {e}")
    # --- END DEBUGGING ---

    # Extract fund_id from the input schema
    fund_id = trade_in.fund_id # This is the line causing the error
    if not fund_id:
         log.error(f"Fund ID missing for trade transaction type {trade_in.transaction_type}")
         raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Fund ID is required for trade transactions.")

    log.info(f"Processing trade transaction for fund {fund_id}, asset {trade_in.asset_id}, type {trade_in.transaction_type}")

    # --- 1. Fetch Core Objects ---
    fund = await crud_fund.get_fund(db=db, fund_id=fund_id) # [cite: backend_files/crud/fund.py]
    if not fund:
        log.warning(f"Fund not found: {fund_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fund with id {fund_id} not found.")

    asset = await crud_asset.get_asset(db=db, asset_id=trade_in.asset_id) # [cite: backend_files/crud/asset.py]
    if not asset:
        log.warning(f"Asset not found: {trade_in.asset_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset with id {trade_in.asset_id} not found.")

    # --- 2. Initial Validation & Calculations ---
    trade_type = trade_in.transaction_type
    quantity = trade_in.quantity
    price = trade_in.price_per_unit
    fees = trade_in.fees_commissions or Decimal("0.0") # Ensure fees is Decimal

    # Calculate gross amount (quantity * price) - Pydantic schema might enforce quantity/price presence
    gross_amount = quantity * price

    # Calculate net cash effect (+ for sell, - for buy)
    if trade_type in BUY_TYPES:
        net_cash_effect = -(gross_amount + fees)
        quantity_change = quantity # Positive change for buys
    elif trade_type in SELL_TYPES:
        net_cash_effect = gross_amount - fees
        quantity_change = -quantity # Negative change for sells
    else:
        # Should be caught by schema validation, but handle defensively
        log.error(f"Invalid transaction type '{trade_type}' passed to process_trade_transaction.")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid transaction type for a trade.")

    # --- 3. Pre-Transaction Validation (Cash Check for Buys) ---
    # Quantity check for sells is now handled within _update_or_create_position helper
    if trade_type in BUY_TYPES:
        required_cash = abs(net_cash_effect)
        if fund.brokerage_cash_balance < required_cash: # [cite: backend_files/models/fund.py]
            log.warning(f"Insufficient funds for buy transaction in fund {fund_id}. Required: {required_cash}, Available: {fund.brokerage_cash_balance}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient funds. Required: {required_cash:.2f}, Available: {fund.brokerage_cash_balance:.2f}"
            )

    # --- 4. Create Transaction Record ---
    transaction_data = {
        "club_id": fund.club_id,
        "fund_id": fund_id,
        "asset_id": asset.id, # [cite: backend_files/models/asset.py]
        "transaction_type": trade_type,
        "transaction_date": trade_in.transaction_date, # [cite: backend_files/schemas/transaction.py]
        "quantity": quantity, # The quantity of the trade itself
        "price_per_unit": price,
        "total_amount": gross_amount, # Store gross amount in transaction
        "fees_commissions": fees,
        "description": trade_in.description, # [cite: backend_files/schemas/transaction.py]
        # related_transaction_id, reverses_transaction_id are not typically set for basic trades
    }

    try:
        created_transaction = await crud_transaction.create_transaction(db=db, transaction_data=transaction_data) # [cite: backend_files/crud/transaction.py]
        log.info(f"Created transaction record {created_transaction.id} for fund {fund_id}, asset {asset.id}")

        # --- 5. Update Position using Helper ---
        await _update_or_create_position(
            db=db,
            fund_id=fund_id,
            asset_id=asset.id,
            quantity_change=quantity_change, # Pass the calculated change (+/-)
            price_per_unit=price # Pass price for cost basis calc on buys
        )

        # --- 6. Update Fund Cash Balance ---
        log.info(f"Updating fund {fund_id} cash balance by {net_cash_effect:.2f}")
        fund.brokerage_cash_balance += net_cash_effect # Update the model attribute directly
        db.add(fund) # Add updated fund to the session

        # --- 7. Flush (Optional but good practice) ---
        await db.flush()

        log.info(f"Successfully processed trade transaction {created_transaction.id}")
        return created_transaction

    except IntegrityError as e:
        log.exception(f"Database integrity error during trade processing for fund {fund_id}, asset {asset.id}: {e}")
        await db.rollback() # Rollback the entire operation on integrity error
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Database conflict processing trade: {e}")
    except HTTPException as e:
         # Re-raise known HTTP exceptions from validation steps
         await db.rollback()
         raise e
    except Exception as e:
        log.exception(f"Unexpected error processing trade for fund {fund_id}, asset {asset.id}: {e}")
        await db.rollback() # Rollback on any other error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred processing the trade.")


async def process_cash_receipt_transaction(
    db: AsyncSession,
    *,
    cash_receipt_in: TransactionCreateDividendBrokerageInterest
) -> Transaction:
    """
    Processes a cash receipt transaction (Dividend, Brokerage Interest),
    creates the transaction record, and adjusts the fund's cash balance.
    """
    tx_type = cash_receipt_in.transaction_type
    fund_id = cash_receipt_in.fund_id
    asset_id = cash_receipt_in.asset_id # Can be None
    amount = cash_receipt_in.total_amount
    fees = cash_receipt_in.fees_commissions or Decimal("0.0") # Ensure fees is Decimal

    log.info(f"Processing cash receipt transaction for fund {fund_id}, asset {asset_id}, type {tx_type}, amount {amount}")

    # --- 1. Validate Fund ID ---
    if not fund_id:
        # This should be caught by schema validation based on type
        log.error(f"Fund ID missing for cash receipt transaction type {tx_type}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Fund ID is required for this transaction type.")

    fund = await crud_fund.get_fund(db=db, fund_id=fund_id) # [cite: backend_files/crud/fund.py]
    if not fund:
        log.warning(f"Fund not found: {fund_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fund with id {fund_id} not found.")

    # --- 2. Validate Asset ID based on Type ---
    asset = None # Initialize asset as None
    if tx_type == TransactionType.DIVIDEND:
        if not asset_id:
            log.warning(f"Asset ID missing for DIVIDEND transaction in fund {fund_id}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Asset ID is required for Dividend transactions.")
        asset = await crud_asset.get_asset(db=db, asset_id=asset_id) # [cite: backend_files/crud/asset.py]
        if not asset:
            log.warning(f"Asset not found: {asset_id} for DIVIDEND transaction")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Asset with id {asset_id} not found.")
    elif tx_type == TransactionType.BROKERAGE_INTEREST:
        if asset_id:
            log.warning(f"Asset ID provided ({asset_id}) for BROKERAGE_INTEREST transaction, but it should be null.")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Asset ID must be null for Brokerage Interest transactions.")
    else:
        # Should not happen if called correctly, but defensive check
        log.error(f"Invalid transaction type '{tx_type}' passed to process_cash_receipt_transaction.")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid transaction type for cash receipt.")

    # --- 3. Prepare Transaction Data ---
    # Cash receipts increase the balance
    net_cash_effect = amount - fees # Subtract fees if any apply

    transaction_data = {
        "club_id": fund.club_id,
        "fund_id": fund_id,
        "asset_id": asset_id, # Will be None for Brokerage Interest
        "transaction_type": tx_type,
        "transaction_date": cash_receipt_in.transaction_date, # [cite: backend_files/schemas/transaction.py]
        "quantity": None, # Not applicable
        "price_per_unit": None, # Not applicable
        "total_amount": amount, # Store the gross amount received
        "fees_commissions": fees,
        "description": cash_receipt_in.description, # [cite: backend_files/schemas/transaction.py]
    }

    try:
        # --- 4. Create Transaction Record ---
        created_transaction = await crud_transaction.create_transaction(db=db, transaction_data=transaction_data) # [cite: backend_files/crud/transaction.py]
        log.info(f"Created transaction record {created_transaction.id} for cash receipt in fund {fund_id}")

        # --- 5. Update Fund Cash Balance ---
        log.info(f"Updating fund {fund_id} cash balance by {net_cash_effect:.2f}")
        fund.brokerage_cash_balance += net_cash_effect # Update the model attribute directly
        db.add(fund) # Add updated fund to the session

        # --- 6. Flush (Optional but good practice) ---
        await db.flush()

        log.info(f"Successfully processed cash receipt transaction {created_transaction.id}")
        return created_transaction

    except IntegrityError as e:
        log.exception(f"Database integrity error during cash receipt processing for fund {fund_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Database conflict processing cash receipt: {e}")
    except HTTPException as e:
         await db.rollback()
         raise e
    except Exception as e:
        log.exception(f"Unexpected error processing cash receipt for fund {fund_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred processing the cash receipt.")


async def process_cash_transfer_transaction(
    db: AsyncSession,
    *,
    transfer_in: TransactionCreateCashTransfer,
    club_id: uuid.UUID
) -> Transaction | Sequence[Transaction] | None:
    """
    Processes a cash transfer transaction (Bank<->Brokerage, Interfund),
    creates the transaction record(s), and adjusts relevant cash balances.
    If type is BANK_TO_BROKERAGE, distributes cash to funds based on FundSplits.
    """
    tx_type = transfer_in.transaction_type
    amount = transfer_in.total_amount
    log.info(f"Processing cash transfer for club {club_id}, type {tx_type}, amount {amount}")
    club = await crud_club.get_club(db=db, club_id=club_id) # [cite: backend_files/crud/club.py]
    if not club: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Club with id {club_id} not found.")
    fees = transfer_in.fees_commissions or Decimal("0.0"); total_deduction = amount + fees
    if tx_type == TransactionType.BANK_TO_BROKERAGE:
        if club.bank_account_balance < total_deduction: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Insufficient funds in club bank account. Required: {total_deduction:.2f}, Available: {club.bank_account_balance:.2f}")
    elif tx_type == TransactionType.BROKERAGE_TO_BANK or tx_type == TransactionType.INTERFUND_CASH_TRANSFER:
        fund_id = transfer_in.fund_id
        if not fund_id: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Source fund_id is required.")
        source_fund = await crud_fund.get_fund(db=db, fund_id=fund_id) # [cite: backend_files/crud/fund.py]
        if not source_fund: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source fund with id {fund_id} not found.")
        if source_fund.club_id != club_id: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Source fund does not belong to the specified club.")
        if source_fund.brokerage_cash_balance < total_deduction: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Insufficient funds in source fund '{source_fund.name}'. Required: {total_deduction:.2f}, Available: {source_fund.brokerage_cash_balance:.2f}")

    try:
        if tx_type == TransactionType.BANK_TO_BROKERAGE:
            fund_splits = await crud_fund_split.get_fund_splits_by_club(db=db, club_id=club.id) # [cite: backend_files/crud/fund_split.py]
            if not fund_splits: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot process BANK_TO_BROKERAGE: No fund splits defined for this club.")
            total_split_percentage = sum(fs.split_percentage for fs in fund_splits) # [cite: backend_files/models/fund_split.py]
            if total_split_percentage > Decimal("1.0"): raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Fund split percentages exceed 100% ({total_split_percentage*100}%). Cannot distribute transfer.")
            log.info(f"Distributing BANK_TO_BROKERAGE amount {amount} according to fund splits.")
            distributed_amount_total = Decimal("0.0"); created_transactions: list[Transaction] = []
            club.bank_account_balance -= total_deduction; db.add(club); log.info(f"Decreased club {club_id} bank balance by {total_deduction}")
            fee_applied = False
            for i, split in enumerate(fund_splits):
                split_amount = (amount * split.split_percentage).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                distributed_amount_total += split_amount
                if distributed_amount_total > amount and i == len(fund_splits) - 1: split_amount -= (distributed_amount_total - amount); log.warning(f"Adjusting final split amount by {-(distributed_amount_total - amount)} due to rounding.")
                if split_amount <= Decimal("0"): log.warning(f"Skipping split for fund {split.fund_id} as calculated amount is zero or less."); continue
                target_fund = await crud_fund.get_fund(db=db, fund_id=split.fund_id) # [cite: backend_files/crud/fund.py]
                if not target_fund: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target fund {split.fund_id} for split not found.")
                if target_fund.club_id != club_id: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Target fund {target_fund.id} does not belong to club {club_id}.")
                current_fees = fees if not fee_applied else Decimal("0.0")
                transfer_tx_data = {"club_id": club_id, "fund_id": target_fund.id, "asset_id": None, "transaction_type": TransactionType.BANK_TO_BROKERAGE, "transaction_date": transfer_in.transaction_date, "quantity": None, "price_per_unit": None, "total_amount": split_amount, "fees_commissions": current_fees, "description": transfer_in.description or f"Transfer to {target_fund.name} based on fund split ({split.split_percentage*100:.2f}%)"}
                created_tx = await crud_transaction.create_transaction(db=db, transaction_data=transfer_tx_data) # [cite: backend_files/crud/transaction.py]
                created_transactions.append(created_tx)
                if fees > 0: fee_applied = True
                target_fund.brokerage_cash_balance += split_amount; db.add(target_fund); log.info(f"Created BANK_TO_BROKERAGE tx {created_tx.id}, increased fund {target_fund.id} brokerage by {split_amount}")
            remainder = amount - distributed_amount_total
            if remainder > Decimal("0.00"): log.warning(f"Transfer amount {amount} was not fully distributed due to splits < 100% or rounding. Remainder: {remainder}. Leaving remainder in bank account."); club.bank_account_balance += remainder; db.add(club); log.info(f"Adjusted club bank balance by {remainder} due to undistributed amount.")
            await db.flush()
            
            # Eagerly load relationships to prevent MissingGreenlet errors during serialization
            for tx in created_transactions:
                await db.refresh(tx, ['fund', 'asset'])
                log.info(f"Refreshed transaction {tx.id} with fund and asset relationships")
                
            return created_transactions
        elif tx_type == TransactionType.BROKERAGE_TO_BANK:
            fund_id = transfer_in.fund_id; source_fund = await crud_fund.get_fund(db=db, fund_id=fund_id);
            if not source_fund: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source fund {fund_id} not found.")
            transaction_data = {"club_id": club_id, "fund_id": fund_id, "asset_id": None, "transaction_type": tx_type, "transaction_date": transfer_in.transaction_date, "quantity": None, "price_per_unit": None, "total_amount": amount, "fees_commissions": fees, "description": transfer_in.description}
            created_transaction = await crud_transaction.create_transaction(db=db, transaction_data=transaction_data)
            source_fund.brokerage_cash_balance -= total_deduction; club.bank_account_balance += amount; db.add(source_fund); db.add(club); log.info(f"Decreased fund {source_fund.id} brokerage by {total_deduction}, increased club {club_id} bank by {amount}")
            await db.flush()
            
            # Eagerly load relationships to prevent MissingGreenlet errors during serialization
            await db.refresh(created_transaction, ['fund', 'asset'])
            log.info(f"Refreshed transaction {created_transaction.id} with fund and asset relationships")
            
            return created_transaction
        elif tx_type == TransactionType.INTERFUND_CASH_TRANSFER:
            fund_id = transfer_in.fund_id; target_fund_id = transfer_in.target_fund_id
            if not target_fund_id: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Target fund_id is required.")
            source_fund = await crud_fund.get_fund(db=db, fund_id=fund_id); target_fund = await crud_fund.get_fund(db=db, fund_id=target_fund_id)
            if not source_fund or not target_fund: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source or target fund not found.")
            transaction_data = {"club_id": club_id, "fund_id": fund_id, "asset_id": None, "transaction_type": tx_type, "transaction_date": transfer_in.transaction_date, "quantity": None, "price_per_unit": None, "total_amount": amount, "fees_commissions": fees, "description": transfer_in.description or f"Transfer to fund {target_fund.name}"}
            created_transaction = await crud_transaction.create_transaction(db=db, transaction_data=transaction_data)
            source_fund.brokerage_cash_balance -= total_deduction; target_fund.brokerage_cash_balance += amount; db.add(source_fund); db.add(target_fund); log.info(f"Decreased fund {source_fund.id} brokerage by {total_deduction}, increased fund {target_fund.id} brokerage by {amount}")
            await db.flush()
            
            # Eagerly load relationships to prevent MissingGreenlet errors during serialization
            await db.refresh(created_transaction, ['fund', 'asset'])
            log.info(f"Refreshed transaction {created_transaction.id} with fund and asset relationships")
            
            return created_transaction
    except IntegrityError as e: log.exception(f"Database integrity error during cash transfer processing for club {club_id}: {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Database conflict processing cash transfer: {e}")
    except HTTPException as e: await db.rollback(); raise e
    except Exception as e: log.exception(f"Unexpected error processing cash transfer for club {club_id}: {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred processing the cash transfer.")


async def process_option_lifecycle_transaction(
    db: AsyncSession,
    *,
    lifecycle_in: TransactionCreateOptionLifecycle
) -> Transaction:
    """ Processes an option lifecycle transaction. (Implementation omitted for brevity) """
    # ... (implementation as before) ...
    tx_type = lifecycle_in.transaction_type; fund_id = lifecycle_in.fund_id; option_asset_id = lifecycle_in.asset_id; quantity = lifecycle_in.quantity; fees = lifecycle_in.fees_commissions or Decimal("0.0")
    log.info(f"Processing option lifecycle transaction for fund {fund_id}, option asset {option_asset_id}, type {tx_type}, quantity {quantity}")
    fund = await crud_fund.get_fund(db=db, fund_id=fund_id);
    if not fund: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fund {fund_id} not found.")
    option_asset = await crud_asset.get_asset(db=db, asset_id=option_asset_id);
    if not option_asset: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Option asset {option_asset_id} not found.")
    if option_asset.asset_type != "Option": raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Asset provided is not an option.")
    if not option_asset.underlying_asset_id or not option_asset.strike_price or not option_asset.option_type: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Option asset details (underlying_id, strike, type) missing.")
    underlying_asset = await crud_asset.get_asset(db=db, asset_id=option_asset.underlying_asset_id);
    if not underlying_asset: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Underlying asset {option_asset.underlying_asset_id} not found.")
    option_position = await crud_position.get_position_by_fund_and_asset(db=db, fund_id=fund_id, asset_id=option_asset_id);
    if not option_position: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Position for option asset {option_asset_id} in fund {fund_id} not found.")
    if option_position.quantity > 0:
        if quantity > option_position.quantity: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Quantity ({quantity}) exceeds available long position quantity ({option_position.quantity}).")
        option_quantity_change = -quantity
    elif option_position.quantity < 0:
         if quantity > abs(option_position.quantity): raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Quantity ({quantity}) exceeds available short position quantity ({abs(option_position.quantity)}).")
         option_quantity_change = quantity
    else: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot process lifecycle event on a zero quantity option position.")
    primary_tx_data = {"club_id": fund.club_id, "fund_id": fund_id, "asset_id": option_asset_id, "transaction_type": tx_type, "transaction_date": lifecycle_in.transaction_date, "quantity": quantity, "price_per_unit": None, "total_amount": None, "fees_commissions": fees, "description": lifecycle_in.description, "related_transaction_id": None, "reverses_transaction_id": None}
    linked_stock_tx: Transaction | None = None; stock_quantity_change: Decimal = Decimal("0"); stock_price: Decimal = option_asset.strike_price; cash_change_from_stock: Decimal = Decimal("0"); shares_per_contract = Decimal("100")
    try:
        primary_tx = await crud_transaction.create_transaction(db=db, transaction_data=primary_tx_data)
        log.info(f"Created primary option lifecycle transaction {primary_tx.id} ({tx_type})")
        await _update_or_create_position(db=db, fund_id=fund_id, asset_id=option_asset_id, quantity_change=option_quantity_change, price_per_unit=Decimal("0.0"))
        log.info(f"Updated option position {option_position.id} quantity by {option_quantity_change}")
        stock_tx_type: TransactionType | None = None; stock_tx_data: Dict[str, Any] | None = None
        if tx_type == TransactionType.OPTION_EXERCISE:
            if option_asset.option_type == OptionType.CALL: stock_tx_type = TransactionType.BUY_STOCK; stock_quantity_change = quantity * shares_per_contract; cash_change_from_stock = -(stock_quantity_change * stock_price)
            elif option_asset.option_type == OptionType.PUT: stock_tx_type = TransactionType.SELL_STOCK; stock_quantity_change = -(quantity * shares_per_contract); cash_change_from_stock = abs(stock_quantity_change * stock_price)
        elif tx_type == TransactionType.OPTION_ASSIGNMENT:
             if option_asset.option_type == OptionType.CALL: stock_tx_type = TransactionType.SELL_STOCK; stock_quantity_change = -(quantity * shares_per_contract); cash_change_from_stock = abs(stock_quantity_change * stock_price)
             elif option_asset.option_type == OptionType.PUT: stock_tx_type = TransactionType.BUY_STOCK; stock_quantity_change = quantity * shares_per_contract; cash_change_from_stock = -(stock_quantity_change * stock_price)
        if stock_tx_type and underlying_asset:
            stock_tx_data = {"club_id": fund.club_id, "fund_id": fund_id, "asset_id": underlying_asset.id, "transaction_type": stock_tx_type, "transaction_date": lifecycle_in.transaction_date, "quantity": abs(stock_quantity_change), "price_per_unit": stock_price, "total_amount": abs(stock_quantity_change * stock_price), "fees_commissions": Decimal("0.0"), "description": f"{tx_type.value} of {quantity} contract(s) {option_asset.symbol}", "related_transaction_id": primary_tx.id}
            linked_stock_tx = await crud_transaction.create_transaction(db=db, transaction_data=stock_tx_data)
            log.info(f"Created linked stock transaction {linked_stock_tx.id} ({stock_tx_type}) related to {primary_tx.id}")
            await _update_or_create_position(db=db, fund_id=fund_id, asset_id=underlying_asset.id, quantity_change=stock_quantity_change, price_per_unit=stock_price)
            log.info(f"Updated stock position for asset {underlying_asset.id} quantity by {stock_quantity_change}")
        net_cash_change = cash_change_from_stock - fees
        log.info(f"Updating fund {fund_id} cash balance by {net_cash_change:.2f} (Stock: {cash_change_from_stock}, Fees: {-fees})")
        fund.brokerage_cash_balance += net_cash_change; db.add(fund)
        await db.flush()
        log.info(f"Successfully processed option lifecycle transaction {primary_tx.id}")
        return primary_tx
    except IntegrityError as e: log.exception(f"Database integrity error during option lifecycle processing for fund {fund_id}, option {option_asset_id}: {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Database conflict processing option lifecycle event: {e}")
    except HTTPException as e: await db.rollback(); raise e
    except Exception as e: log.exception(f"Unexpected error processing option lifecycle event for fund {fund_id}, option {option_asset_id}: {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred processing the option lifecycle event.")


async def process_club_expense_transaction(
    db: AsyncSession,
    *,
    expense_in: TransactionCreateClubExpense,
    club_id: uuid.UUID
) -> Transaction:
    """
    Process a club expense transaction.
    
    Args:
        db: Database session
        expense_in: Club expense data
        club_id: ID of the club
        
    Returns:
        Created transaction
        
    Raises:
        HTTPException: If club not found or insufficient balance
    """
    try:
        # Fetch the club
        club = await crud_club.get_club(db=db, club_id=club_id)
        if not club:
            log.error(f"Club with ID {club_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Club with ID {club_id} not found",
            )
            
        # Validate transaction type
        if expense_in.transaction_type != TransactionType.CLUB_EXPENSE:
            log.error(f"Invalid transaction type: {expense_in.transaction_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction type must be CLUB_EXPENSE",
            )
            
        # Calculate total deduction
        total_deduction = expense_in.total_amount + expense_in.fees_commissions
        
        # Check if club has sufficient balance
        if club.bank_account_balance < total_deduction:
            log.error(f"Insufficient balance: {club.bank_account_balance} < {total_deduction}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient club bank account balance",
            )
            
        # Create transaction data
        transaction_data = {
            "club_id": club_id,
            "fund_id": None,
            "asset_id": None,
            "transaction_type": TransactionType.CLUB_EXPENSE,
            "total_amount": expense_in.total_amount,
            "fees_commissions": expense_in.fees_commissions,
            "description": expense_in.description,
            "transaction_date": expense_in.transaction_date,
        }
        
        # Create the transaction
        transaction = await crud_transaction.create_transaction(db=db, transaction_data=transaction_data)
        
        # Update club balance
        club.bank_account_balance -= total_deduction
        db.add(club)
        await db.flush()
        
        return transaction
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and re-raise other exceptions
        log.exception(f"Error processing club expense: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing club expense: {str(e)}",
        )

# --- Transaction Retrieval Services ---

async def get_transaction_by_id(db: AsyncSession, transaction_id: uuid.UUID) -> Transaction:
    """ Retrieves a single transaction by its ID. """
    log.debug(f"Attempting to retrieve transaction with ID: {transaction_id}")
    transaction = await crud_transaction.get_transaction(db=db, transaction_id=transaction_id)
    if not transaction: log.warning(f"Transaction not found: {transaction_id}"); raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transaction with id {transaction_id} not found.")
    log.debug(f"Successfully retrieved transaction {transaction_id}")
    return transaction


async def list_transactions(
    db: AsyncSession,
    *,
    club_id: uuid.UUID, # Added club_id for filtering
    fund_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100
) -> Sequence[Transaction]:
    """
    Retrieves a list of transactions with optional filtering and pagination.
    Ensures transactions belong to the specified club.
    """
    log.debug(f"Listing transactions for club {club_id} with filters - fund_id: {fund_id}, asset_id: {asset_id}, skip: {skip}, limit: {limit}")
    # **FIX:** Pass club_id to CRUD function for proper filtering
    # TODO: Update crud_transaction.get_multi_transactions to accept and use club_id
    transactions = await crud_transaction.get_multi_transactions(
        db=db,
        club_id=club_id, # Pass club_id
        fund_id=fund_id,
        asset_id=asset_id,
        skip=skip,
        limit=limit
    ) # [cite: backend_files/crud/transaction.py] - Needs update in CRUD
    log.debug(f"Retrieved {len(transactions)} transactions.")
    return transactions

