# backend/tests/crud/test_position.py

import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Import refactored CRUD function
from backend.crud import position as crud_position
# Models needed
from backend.models import Club, User, Fund, Asset, Position
# No schemas needed for basic Position CRUD tests

# Import refactored test helpers for prerequisites
from .test_user import create_test_user
from .test_club import create_test_club_via_crud
from .test_asset import create_test_stock_asset_via_crud # Use refactored helper
from .test_fund import create_test_fund_via_crud # Use refactored helper

pytestmark = pytest.mark.asyncio(loop_scope="function")


# --- Test Setup Helpers ---

async def setup_basic_position_context(db_session: AsyncSession):
    """Creates prerequisite Fund and Asset for position tests using refactored helpers."""
    # Ensure unique users/creators
    creator = await create_test_user(db_session, email=f"pos_creator_{uuid.uuid4()}@example.com", auth0_sub=f"auth0|pos_cr_{uuid.uuid4()}")
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Fix: Create fund explicitly instead of relying on default
    fund = await create_test_fund_via_crud(db_session, club=club, name="Position Test Fund")
    asset = await create_test_stock_asset_via_crud(db_session, symbol="XYZ", name="XYZ Corp")
    return fund, asset # Return fund and asset objects

# Helper prepares data dict for refactored create_position
async def create_test_position_via_crud(
    db_session: AsyncSession,
    fund: Fund,
    asset: Asset,
    quantity: Decimal = Decimal("0.0"),
    avg_cost: Decimal = Decimal("0.0")
) -> Position:
    """Helper prepares data dict and calls refactored create_position."""
    position_data = {
        "fund_id": fund.id,
        "asset_id": asset.id,
        "quantity": quantity,
        "average_cost_basis": avg_cost
    }
    return await crud_position.create_position(db=db_session, position_data=position_data)


# --- Tests ---

async def test_create_position(db_session: AsyncSession):
    """Tests the internal creation of a position with default values."""
    fund, asset = await setup_basic_position_context(db_session)
    # Use the helper which calls the refactored CRUD
    created_position = await create_test_position_via_crud(db_session, fund, asset) # Uses defaults

    assert created_position is not None
    assert created_position.fund_id == fund.id
    assert created_position.asset_id == asset.id
    # Check default values set by the CRUD function or model
    assert created_position.quantity == Decimal("0.0")
    assert created_position.average_cost_basis == Decimal("0.0")
    assert created_position.id is not None


async def test_create_position_with_initial_values(db_session: AsyncSession):
    """Tests the internal creation of a position with specified values."""
    fund, asset = await setup_basic_position_context(db_session)
    qty = Decimal("100.0")
    cost = Decimal("50.25")
    # Use the helper which calls the refactored CRUD
    created_position = await create_test_position_via_crud(
        db_session, fund, asset, quantity=qty, avg_cost=cost
    )

    assert created_position is not None
    assert created_position.quantity == qty
    assert created_position.average_cost_basis == cost


async def test_get_position(db_session: AsyncSession):
    """Tests retrieving a single position by its ID."""
    fund, asset = await setup_basic_position_context(db_session)
    # Use the helper
    created_position = await create_test_position_via_crud(db_session, fund, asset)

    retrieved_position = await crud_position.get_position(db=db_session, position_id=created_position.id)

    assert retrieved_position is not None
    assert retrieved_position.id == created_position.id
    assert retrieved_position.fund_id == fund.id
    assert retrieved_position.asset_id == asset.id


async def test_get_position_not_found(db_session: AsyncSession):
    """Tests retrieving a non-existent position ID."""
    non_existent_id = uuid.uuid4()
    retrieved_position = await crud_position.get_position(db=db_session, position_id=non_existent_id)
    assert retrieved_position is None


async def test_get_position_by_fund_and_asset(db_session: AsyncSession):
    """Tests retrieving a position using fund_id and asset_id."""
    fund, asset = await setup_basic_position_context(db_session)
    # Use the helper
    created_position = await create_test_position_via_crud(db_session, fund, asset)

    retrieved_position = await crud_position.get_position_by_fund_and_asset(
        db=db_session, fund_id=fund.id, asset_id=asset.id
    )

    assert retrieved_position is not None
    assert retrieved_position.id == created_position.id


async def test_get_multi_positions_by_fund(db_session: AsyncSession):
    """Tests retrieving multiple positions filtered by fund_id."""
    fund, asset1 = await setup_basic_position_context(db_session)
    # Create additional assets using refactored helper
    asset2 = await create_test_stock_asset_via_crud(db_session, symbol="ABC", name="ABC Inc")
    asset3 = await create_test_stock_asset_via_crud(db_session, symbol="DEF", name="DEF Ltd")

    # Use the helper to create positions
    pos1 = await create_test_position_via_crud(db_session, fund, asset1)
    pos2 = await create_test_position_via_crud(db_session, fund, asset2)
    pos3 = await create_test_position_via_crud(db_session, fund, asset3)

    # Create another fund and position to ensure filtering
    # Ensure unique users/creators
    creator2 = await create_test_user(db_session, email=f"f2_{uuid.uuid4()}@f.com", auth0_sub=f"auth0|f2_pos_{uuid.uuid4()}")
    club2 = await create_test_club_via_crud(db_session, creator=creator2, name="Club 2")
    fund2 = await create_test_fund_via_crud(db_session, club=club2, name="Fund 2")
    # Use helper to create position in different fund
    await create_test_position_via_crud(db_session, fund2, asset1)

    positions_fund1 = await crud_position.get_multi_positions(db=db_session, fund_id=fund.id, limit=10)

    assert len(positions_fund1) == 3
    assert {p.id for p in positions_fund1} == {pos1.id, pos2.id, pos3.id}


async def test_delete_position(db_session: AsyncSession):
    """Tests the internal deletion of a position."""
    fund, asset = await setup_basic_position_context(db_session)
    # Use helper
    created_position = await create_test_position_via_crud(db_session, fund, asset)
    position_id = created_position.id

    # Ensure no dependencies (Transactions) exist if FK constraints are strict
    # Test the delete CRUD function directly
    deleted_position = await crud_position.delete_position(db=db_session, db_obj=created_position)
    assert deleted_position.id == position_id

    # Verify it's gone from DB
    retrieved = await crud_position.get_position(db=db_session, position_id=position_id)
    assert retrieved is None


async def test_create_duplicate_position_fails(db_session: AsyncSession):
    """Tests the database unique constraint (fund_id, asset_id)."""
    # Assumes unique constraint on (fund_id, asset_id) exists in DB model
    fund, asset = await setup_basic_position_context(db_session)
    # Use the helper to create the first position
    await create_test_position_via_crud(db_session, fund, asset)

    # Try creating the same position again by calling create_position directly
    position_data_dup = {
        "fund_id": fund.id,
        "asset_id": asset.id
        # quantity/avg_cost will use defaults
    }
    with pytest.raises(IntegrityError):
         await crud_position.create_position(db=db_session, position_data=position_data_dup)

# Test for internal update function is removed/commented as direct updates are unlikely
# async def test_update_position_internal(db_session: AsyncSession): ...

