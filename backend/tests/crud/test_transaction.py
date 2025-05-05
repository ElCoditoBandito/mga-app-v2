# backend/tests/crud/test_transaction.py

import uuid
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# CRUD functions being tested (refactored)
from backend.crud import transaction as crud_tx
# Helpers/Models/CRUD for prerequisites
from backend.crud import fund as crud_fund
from backend.crud import asset as crud_asset
from backend.crud import position as crud_position # Needed if position CRUD exists
from backend.models import Club, User, Fund, Asset, Position, Transaction
from backend.models.enums import AssetType, OptionType, TransactionType # Import all needed enums

# No longer need specific TransactionCreate schemas for direct CRUD testing
# from backend.schemas import (...)

# Import refactored test helpers for prerequisites
from .test_user import create_test_user
from .test_club import create_test_club_via_crud # Use refactored helper
# Use refactored asset helpers
from .test_asset import create_test_stock_asset_via_crud, create_test_option_asset_via_crud # Use refactored helpers
from .test_fund import create_test_fund_via_crud # Use refactored helper
# Use the internal helper from test_position to create position for testing
# Ensure this helper is updated if needed based on test_position changes
from .test_position import create_test_position_via_crud # Assumes this works or is refactored


pytestmark = pytest.mark.asyncio(loop_scope="function")


# --- Test Setup Helpers ---

async def setup_fund_asset_position(
    db_session: AsyncSession,
    asset_type: AssetType = AssetType.STOCK,
    option_details: dict | None = None # For creating option assets/positions
) -> tuple[Fund, Asset, Position]:
    """Creates prerequisite Fund, Asset (Stock/Option), and Position using refactored helpers."""
    # Fix: Remove invalid 'username' argument
    creator = await create_test_user(db_session, email=f"tx_creator_{uuid.uuid4()}@test.com", auth0_sub=f"auth0|tx_creator_{uuid.uuid4()}")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Get the fund (assuming default exists or create one)
    # Using get_fund_by_club_and_name assumes a default fund was created elsewhere or needs creation here.
    # Let's create a fund explicitly for clarity in this helper.
    fund = await create_test_fund_via_crud(db_session, club=club, name="Transaction Test Fund")
    # fund = await crud_fund.get_fund_by_club_and_name(
    #     db=db_session, club_id=club.id, name="Default Fund" # This might fail if default isn't created
    # )
    # assert fund is not None, "Fund needed for transaction tests was not found/created."

    # Ensure option_details is a dict if asset_type is OPTION
    if asset_type == AssetType.OPTION and option_details is None:
        option_details = {} # Default to empty dict if None

    if asset_type == AssetType.OPTION:
        # Need an underlying stock first (use refactored helper)
        underlying_stock = await create_test_stock_asset_via_crud(db_session, symbol=f"UND_{uuid.uuid4()}"[:10])
        # Create the option asset (use refactored helper)
        opt_symbol = f"OPT_{uuid.uuid4()}"[:10]
        asset = await create_test_option_asset_via_crud(
            db_session,
            underlying_asset=underlying_stock,
            symbol=opt_symbol,
            option_type=option_details.get("option_type", OptionType.CALL), # Now safe to call .get()
            strike_price=option_details.get("strike_price", Decimal("100.0")), # Now safe to call .get()
            expiration_date=option_details.get("expiration_date", date.today() + timedelta(days=90)), # Now safe to call .get()
        )
    else: # Default to STOCK (use refactored helper)
        asset = await create_test_stock_asset_via_crud(db_session, symbol=f"STK_{uuid.uuid4()}"[:10])

    # Use the internal helper from test_position file to create the position
    # Ensure create_test_position is compatible or refactored if needed
    position = await create_test_position_via_crud(db_session, fund=fund, asset=asset)
    return fund, asset, position

# --- Tests for Creating Specific Transaction Types ---

async def test_create_buy_stock(db_session: AsyncSession):
    """Tests creating a BUY_STOCK transaction."""
    fund, asset, position = await setup_fund_asset_position(db_session, asset_type=AssetType.STOCK)
    tx_type = TransactionType.BUY_STOCK
    qty = Decimal("50")
    price = Decimal("120.50")
    tx_date = datetime.now(timezone.utc)
    fees = Decimal("2.99")

    # Prepare data dict for refactored CRUD function
    tx_data = {
        "fund_id": fund.id,
        "asset_id": asset.id,
        "transaction_type": tx_type,
        "transaction_date": tx_date,
        "quantity": qty,
        "price_per_unit": price,
        "fees_commissions": fees,
        "description": "Test Buy Stock"
        # Add other fields from Transaction model if needed (e.g., total_amount if calculated here)
    }
    created_tx = await crud_tx.create_transaction(db=db_session, transaction_data=tx_data)

    assert created_tx is not None
    assert created_tx.fund_id == fund.id
    assert created_tx.asset_id == asset.id
    assert created_tx.transaction_type == tx_type
    assert created_tx.quantity == qty
    assert created_tx.price_per_unit == price
    assert created_tx.fees_commissions == fees
    assert created_tx.id is not None


async def test_create_sell_option(db_session: AsyncSession):
    """Tests creating a SELL_OPTION transaction (SellToOpen)."""
    # Fix: Pass option_details={} to the helper
    fund, asset, position = await setup_fund_asset_position(
        db_session, asset_type=AssetType.OPTION, option_details={}
    )
    tx_type = TransactionType.SELL_OPTION # SellToOpen
    qty = Decimal("2") # 2 contracts
    price = Decimal("1.50") # Premium per contract
    tx_date = datetime.now(timezone.utc)
    fees = Decimal("1.30")

    # Prepare data dict for refactored CRUD function
    tx_data = {
        "fund_id": fund.id,
        "asset_id": asset.id,
        "transaction_type": tx_type,
        "transaction_date": tx_date,
        "quantity": qty,
        "price_per_unit": price,
        "fees_commissions": fees,
        "description": "Test Sell Option (STO)"
    }
    created_tx = await crud_tx.create_transaction(db=db_session, transaction_data=tx_data)

    assert created_tx is not None
    assert created_tx.fund_id == fund.id
    assert created_tx.asset_id == asset.id
    assert created_tx.transaction_type == tx_type
    assert created_tx.quantity == qty
    assert created_tx.price_per_unit == price


async def test_create_dividend(db_session: AsyncSession):
    """Tests creating a DIVIDEND transaction."""
    fund, asset, position = await setup_fund_asset_position(db_session, asset_type=AssetType.STOCK)
    tx_type = TransactionType.DIVIDEND
    amount = Decimal("55.75")
    tx_date = datetime.now(timezone.utc)

    # Prepare data dict for refactored CRUD function
    tx_data = {
        "fund_id": fund.id,
        "asset_id": asset.id, # Required for Dividend
        "transaction_type": tx_type,
        "transaction_date": tx_date,
        "total_amount": amount,
        "description": "Test Dividend Received"
        # quantity and price_per_unit should be None/omitted
    }
    created_tx = await crud_tx.create_transaction(db=db_session, transaction_data=tx_data)

    assert created_tx is not None
    assert created_tx.fund_id == fund.id
    assert created_tx.asset_id == asset.id # Should have asset_id
    assert created_tx.transaction_type == tx_type
    assert created_tx.total_amount == amount
    assert created_tx.quantity is None # Check model default or DB default
    assert created_tx.price_per_unit is None


async def test_create_brokerage_interest(db_session: AsyncSession):
    """Tests creating a BROKERAGE_INTEREST transaction."""
    fund, _, _ = await setup_fund_asset_position(db_session) # Don't need asset/position directly
    tx_type = TransactionType.BROKERAGE_INTEREST
    amount = Decimal("12.34")
    tx_date = datetime.now(timezone.utc)

    # Prepare data dict for refactored CRUD function
    tx_data = {
        "fund_id": fund.id, # Required
        "asset_id": None, # Must be None for Brokerage Interest
        "transaction_type": tx_type,
        "transaction_date": tx_date,
        "total_amount": amount,
        "description": "Test Brokerage Interest"
    }
    created_tx = await crud_tx.create_transaction(db=db_session, transaction_data=tx_data)

    assert created_tx is not None
    assert created_tx.fund_id == fund.id
    assert created_tx.asset_id is None # Must be None
    assert created_tx.transaction_type == tx_type
    assert created_tx.total_amount == amount


async def test_create_bank_interest(db_session: AsyncSession):
    """Tests creating a BANK_INTEREST transaction (club level)."""
    # No fund/asset/position needed
    tx_type = TransactionType.BANK_INTEREST
    amount = Decimal("5.67")
    tx_date = datetime.now(timezone.utc)

    # Prepare data dict for refactored CRUD function
    tx_data = {
        "fund_id": None, # Must be None
        "asset_id": None, # Must be None
        "transaction_type": tx_type,
        "transaction_date": tx_date,
        "total_amount": amount,
        "description": "Test Bank Interest"
        # target_fund_id is NOT part of the Transaction model
    }
    created_tx = await crud_tx.create_transaction(db=db_session, transaction_data=tx_data)

    assert created_tx is not None
    assert created_tx.fund_id is None # Must be None
    assert created_tx.asset_id is None # Must be None
    assert created_tx.transaction_type == tx_type
    assert created_tx.total_amount == amount


async def test_create_club_expense(db_session: AsyncSession):
    """Tests creating a CLUB_EXPENSE transaction (club level)."""
    tx_type = TransactionType.CLUB_EXPENSE
    amount = Decimal("50.00")
    tx_date = datetime.now(timezone.utc)

    # Prepare data dict for refactored CRUD function
    tx_data = {
        "fund_id": None, # Must be None
        "asset_id": None, # Must be None
        "transaction_type": tx_type,
        "transaction_date": tx_date,
        "total_amount": amount,
        "description": "Test Club Expense - Pizza"
        # target_fund_id is NOT part of the Transaction model
    }
    created_tx = await crud_tx.create_transaction(db=db_session, transaction_data=tx_data)

    assert created_tx is not None
    assert created_tx.fund_id is None # Must be None
    assert created_tx.asset_id is None # Must be None
    assert created_tx.transaction_type == tx_type
    assert created_tx.total_amount == amount


async def test_create_cash_transfer_bank_to_brokerage(db_session: AsyncSession):
    """Tests creating a BANK_TO_BROKERAGE cash transfer."""
    fund, _, _ = await setup_fund_asset_position(db_session) # Need target fund
    tx_type = TransactionType.BANK_TO_BROKERAGE
    amount = Decimal("1000.00")
    tx_date = datetime.now(timezone.utc)

    # Prepare data dict for refactored CRUD function
    tx_data = {
        "fund_id": fund.id, # The target fund_id
        "asset_id": None, # Must be None
        "transaction_type": tx_type,
        "transaction_date": tx_date,
        "total_amount": amount,
        "description": "Test Bank to Brokerage Transfer"
        # target_fund_id is NOT part of the Transaction model
    }
    created_tx = await crud_tx.create_transaction(db=db_session, transaction_data=tx_data)

    assert created_tx is not None
    assert created_tx.fund_id == fund.id # Target fund
    assert created_tx.asset_id is None
    assert created_tx.transaction_type == tx_type
    assert created_tx.total_amount == amount


async def test_create_option_expiration(db_session: AsyncSession):
    """Tests creating an OPTION_EXPIRATION transaction."""
    # Fix: Pass option_details={} to the helper
    fund, asset, position = await setup_fund_asset_position(
        db_session, asset_type=AssetType.OPTION, option_details={}
    )
    tx_type = TransactionType.OPTION_EXPIRATION
    # Assume entire position expired worthless for test simplicity
    # A real service layer might check position quantity first
    qty = position.quantity if position else Decimal("1.0") # Example quantity
    tx_date = datetime.now(timezone.utc)

    # Prepare data dict for refactored CRUD function
    tx_data = {
        "fund_id": fund.id, # Required
        "asset_id": asset.id, # Required
        "transaction_type": tx_type,
        "transaction_date": tx_date,
        "quantity": qty,
        "description": "Test Option Expiration"
        # price_per_unit and total_amount should be None/omitted
    }
    created_tx = await crud_tx.create_transaction(db=db_session, transaction_data=tx_data)

    assert created_tx is not None
    assert created_tx.fund_id == fund.id
    assert created_tx.asset_id == asset.id
    assert created_tx.transaction_type == tx_type
    assert created_tx.quantity == qty
    assert created_tx.price_per_unit is None
    assert created_tx.total_amount is None


# --- Tests for Get Operations ---

async def test_get_transaction(db_session: AsyncSession):
    """Tests retrieving a single transaction by ID."""
    # Use one of the specific creation methods for setup
    fund, asset, position = await setup_fund_asset_position(db_session)
    tx_data = {
        "fund_id": fund.id, "asset_id": asset.id, "transaction_type": TransactionType.BUY_STOCK,
        "transaction_date": datetime.now(timezone.utc), "quantity": Decimal("10"), "price_per_unit": Decimal("100")
    }
    created_tx = await crud_tx.create_transaction(db=db_session, transaction_data=tx_data)

    # Test the get function
    retrieved_tx = await crud_tx.get_transaction(db=db_session, transaction_id=created_tx.id)

    assert retrieved_tx is not None
    assert retrieved_tx.id == created_tx.id
    assert retrieved_tx.fund_id == fund.id
    assert retrieved_tx.asset_id == asset.id
    assert retrieved_tx.transaction_type == TransactionType.BUY_STOCK


async def test_get_transaction_not_found(db_session: AsyncSession):
    """Tests retrieving a non-existent transaction ID."""
    non_existent_id = uuid.uuid4()
    retrieved_tx = await crud_tx.get_transaction(db=db_session, transaction_id=non_existent_id)
    assert retrieved_tx is None


async def test_get_multi_transactions_by_fund(db_session: AsyncSession):
    """Tests retrieving multiple transactions filtered by fund_id."""
    fund, asset, position = await setup_fund_asset_position(db_session)
    today = datetime.now(timezone.utc)
    tx1_date = today - timedelta(days=2)
    tx2_date = today - timedelta(days=1)
    tx3_date = today

    # Create transactions using data dicts
    tx1_data = {"fund_id": fund.id, "asset_id": asset.id, "transaction_type": TransactionType.BUY_STOCK, "transaction_date": tx1_date, "quantity": Decimal("10"), "price_per_unit": Decimal("90")}
    tx2_data = {"fund_id": fund.id, "asset_id": asset.id, "transaction_type": TransactionType.DIVIDEND, "transaction_date": tx2_date, "total_amount": Decimal("20")}
    tx3_data = {"fund_id": fund.id, "asset_id": asset.id, "transaction_type": TransactionType.SELL_STOCK, "transaction_date": tx3_date, "quantity": Decimal("5"), "price_per_unit": Decimal("110")}

    tx1 = await crud_tx.create_transaction(db=db_session, transaction_data=tx1_data)
    tx2 = await crud_tx.create_transaction(db=db_session, transaction_data=tx2_data)
    tx3 = await crud_tx.create_transaction(db=db_session, transaction_data=tx3_data)

    # Create club-level transaction (should be excluded by fund_id filter)
    exp_data = {"transaction_type": TransactionType.CLUB_EXPENSE, "transaction_date": today, "total_amount": Decimal("10"), "fund_id": None, "asset_id": None}
    await crud_tx.create_transaction(db=db_session, transaction_data=exp_data)

    # Retrieve transactions for the specific fund
    transactions = await crud_tx.get_multi_transactions(db=db_session, fund_id=fund.id, limit=10) # Filter by fund_id

    assert len(transactions) == 3
    # Default order is desc date, desc created_at, desc id
    expected_ids_ordered = [tx3.id, tx2.id, tx1.id] # Assuming creation order matches date order here
    actual_ids_ordered = [tx.id for tx in transactions]
    assert actual_ids_ordered == expected_ids_ordered


# --- (Optional) Tests for Schema Validation via CRUD ---
# These are less relevant now as CRUD expects pre-validated dicts

# No Update/Delete tests typically needed for immutable transactions

