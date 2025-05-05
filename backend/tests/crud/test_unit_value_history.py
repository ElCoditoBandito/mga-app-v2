# backend/tests/crud/test_unit_value_history.py

import uuid
from datetime import date, timedelta, datetime # Import datetime if needed
from decimal import Decimal, getcontext
from typing import Optional # Import Optional

import pytest
import pytest_asyncio
from sqlalchemy import select # Import select for helper check
from sqlalchemy.exc import IntegrityError # If constraint (club_id, valuation_date) exists
from sqlalchemy.ext.asyncio import AsyncSession

# Import the refactored CRUD functions to test
from backend.crud import unit_value_history as crud_uvh
# Import models needed
from backend.models import Club, User, UnitValueHistory # Import relevant models

# Import refactored test helpers for prerequisites
from .test_user import create_test_user
from .test_club import create_test_club_via_crud # Use refactored helper

# Set Decimal precision high enough for tests if needed, though database precision matters more
# getcontext().prec = 30 # Example: Set precision to 30 decimal places

pytestmark = pytest.mark.asyncio(loop_scope="function")


# --- Test Setup Helpers ---

async def setup_basic_uvh_context(db_session: AsyncSession) -> Club:
    """Creates prerequisite Club for unit value history tests using refactored helpers."""
    # Fix: Remove invalid 'username' argument and ensure unique user
    creator = await create_test_user(db_session, email=f"uvh_creator_{uuid.uuid4()}@example.com", auth0_sub=f"auth0|uvh_cr_{uuid.uuid4()}")
    club = await create_test_club_via_crud(db_session, creator=creator)
    return club

# Helper prepares data dict for refactored create_unit_value_history
async def create_test_unit_value_history_via_crud(
    db_session: AsyncSession,
    club: Club, # Use Club object
    valuation_date: date | None = None,
    total_club_value: Decimal = Decimal("10000.00"),
    total_units_outstanding: Decimal = Decimal("1000.00000000"),
    unit_value: Optional[Decimal] = None, # Fix: Accept optional unit_value
) -> UnitValueHistory:
    """
    Helper prepares data dict and calls refactored create_unit_value_history.
    Uses provided unit_value if given, otherwise calculates it.
    """
    if valuation_date is None:
        valuation_date = date.today()

    final_unit_value: Decimal
    if unit_value is not None:
        # Use the provided unit_value
        final_unit_value = unit_value
    else:
        # Calculate unit_value with Decimal precision if not provided
        # Ensure total_units_outstanding is not zero
        if total_units_outstanding == Decimal("0"):
             final_unit_value = Decimal("0.0") # Or handle as error?
        else:
             final_unit_value = total_club_value / total_units_outstanding

    uvh_data = {
        "club_id": club.id,
        "valuation_date": valuation_date,
        "total_club_value": total_club_value,
        "total_units_outstanding": total_units_outstanding,
        "unit_value": final_unit_value, # Use final calculated/provided value
    }
    return await crud_uvh.create_unit_value_history(db=db_session, uvh_data=uvh_data)


# --- Tests ---

async def test_create_unit_value_history(db_session: AsyncSession):
    """Tests the internal creation of a unit value history record."""
    club = await setup_basic_uvh_context(db_session)
    v_date = date(2024, 5, 15)
    tc_value = Decimal("10123.40")
    units = Decimal("1000.12345678")
    # Fix: Calculate expected unit_value using Decimal division for precision
    expected_u_value = tc_value / units

    # Use helper which calls refactored CRUD
    created_uvh = await create_test_unit_value_history_via_crud(
        db_session,
        club=club,
        valuation_date=v_date,
        total_club_value=tc_value,
        total_units_outstanding=units,
        # Let helper calculate unit_value
    )

    assert created_uvh is not None
    assert created_uvh.club_id == club.id
    assert created_uvh.valuation_date == v_date
    assert created_uvh.total_club_value == tc_value
    assert created_uvh.total_units_outstanding == units
    # Fix: Compare Decimal values directly. SQLAlchemy handles DB precision.
    # The stored value might be rounded/truncated by DB based on Numeric(20, 8)
    # Assert that the created value matches the expected calculation within DB precision.
    # Option 1: Direct comparison (might fail if DB truncates differently than Python Decimal)
    # assert created_uvh.unit_value == expected_u_value
    # Option 2: Compare within a small tolerance (less ideal)
    # assert abs(created_uvh.unit_value - expected_u_value) < Decimal("0.00000001")
    # Option 3: Round expected value to match DB precision (Numeric(20, 8))
    expected_u_value_rounded = expected_u_value.quantize(Decimal("0.00000001")) # 8 decimal places
    assert created_uvh.unit_value == expected_u_value_rounded

    assert created_uvh.id is not None


async def test_get_unit_value_history(db_session: AsyncSession):
    """Tests retrieving a single unit value history record by ID."""
    club = await setup_basic_uvh_context(db_session)
    # Use the helper which calls refactored CRUD
    created_uvh = await create_test_unit_value_history_via_crud(db_session, club)

    retrieved_uvh = await crud_uvh.get_unit_value_history(
        db=db_session, unit_value_history_id=created_uvh.id
    )

    assert retrieved_uvh is not None
    assert retrieved_uvh.id == created_uvh.id
    assert retrieved_uvh.club_id == club.id # Check club_id


async def test_get_unit_value_history_not_found(db_session: AsyncSession):
    """Tests retrieving a non-existent unit value history ID."""
    non_existent_id = uuid.uuid4()
    retrieved_uvh = await crud_uvh.get_unit_value_history(
        db=db_session, unit_value_history_id=non_existent_id
    )
    assert retrieved_uvh is None


async def test_get_latest_unit_value_for_club(db_session: AsyncSession):
    """Tests retrieving the latest unit value history for a specific club."""
    club = await setup_basic_uvh_context(db_session)
    today = date.today()
    date1 = today - timedelta(days=2)
    date2 = today - timedelta(days=1) # Should be the latest date
    target_unit_value = Decimal("10.10000000") # Match precision

    # Use the helper to create records - Now passing unit_value is allowed
    uvh1 = await create_test_unit_value_history_via_crud(db_session, club, valuation_date=date1, unit_value=Decimal("9.9")) # Explicit value for testing
    uvh2 = await create_test_unit_value_history_via_crud(db_session, club, valuation_date=date2, unit_value=target_unit_value) # Explicit value for testing
    await create_test_unit_value_history_via_crud(db_session, club, valuation_date=date1 - timedelta(days=1), unit_value=Decimal("9.8")) # Explicit value

    # Create data for another club to ensure filtering
    # Fix: Remove invalid 'username' argument and ensure unique user
    creator2 = await create_test_user(db_session, email=f"f2_{uuid.uuid4()}@u.com", auth0_sub=f"auth0|f2u_{uuid.uuid4()}")
    club2 = await create_test_club_via_crud(db_session, creator=creator2, name="Club UVH2")
    await create_test_unit_value_history_via_crud(db_session, club2, valuation_date=today, unit_value=Decimal("100.0")) # Explicit value

    # Call the refactored CRUD function
    latest_uvh = await crud_uvh.get_latest_unit_value_for_club(db=db_session, club_id=club.id)

    assert latest_uvh is not None
    assert latest_uvh.id == uvh2.id
    assert latest_uvh.valuation_date == date2
    assert latest_uvh.unit_value == target_unit_value


async def test_get_multi_unit_value_history_by_club(db_session: AsyncSession):
    """Tests retrieving multiple unit value history records filtered by club_id."""
    club = await setup_basic_uvh_context(db_session)
    today = date.today()
    date1 = today - timedelta(days=2)
    date2 = today - timedelta(days=1)
    date3 = today

    # Use the helper which calls refactored CRUD
    uvh1 = await create_test_unit_value_history_via_crud(db_session, club, valuation_date=date1)
    uvh2 = await create_test_unit_value_history_via_crud(db_session, club, valuation_date=date2)
    uvh3 = await create_test_unit_value_history_via_crud(db_session, club, valuation_date=date3)

    # Data for another club
    # Fix: Remove invalid 'username' argument and ensure unique user
    creator2 = await create_test_user(db_session, email=f"f3_{uuid.uuid4()}@u.com", auth0_sub=f"auth0|f3u_{uuid.uuid4()}")
    club2 = await create_test_club_via_crud(db_session, creator=creator2, name="Club UVH3")
    await create_test_unit_value_history_via_crud(db_session, club2, valuation_date=today)

    # Call the refactored CRUD function filtering by club_id
    history = await crud_uvh.get_multi_unit_value_history(db=db_session, club_id=club.id, limit=10)

    assert len(history) == 3
    # Default order: desc valuation_date, desc created_at, desc id
    expected_ids_ordered = [uvh3.id, uvh2.id, uvh1.id] # Assuming creation order matches date order
    actual_ids_ordered = [h.id for h in history]
    assert actual_ids_ordered == expected_ids_ordered


async def test_get_multi_unit_value_history_pagination(db_session: AsyncSession):
    """Tests pagination for retrieving unit value history."""
    club = await setup_basic_uvh_context(db_session)
    today = date.today()
    # Use the helper which calls refactored CRUD
    uvh1 = await create_test_unit_value_history_via_crud(db_session, club, valuation_date=today - timedelta(days=2))
    uvh2 = await create_test_unit_value_history_via_crud(db_session, club, valuation_date=today - timedelta(days=1))
    uvh3 = await create_test_unit_value_history_via_crud(db_session, club, valuation_date=today) # Assume created last

    # Get page 1 (limit 2, should be uvh3, uvh2 based on default sorting)
    hist_page1 = await crud_uvh.get_multi_unit_value_history(db=db_session, club_id=club.id, skip=0, limit=2)
    assert len(hist_page1) == 2
    assert hist_page1[0].id == uvh3.id
    assert hist_page1[1].id == uvh2.id

    # Get page 2 (limit 2, skip 2, should be uvh1)
    hist_page2 = await crud_uvh.get_multi_unit_value_history(db=db_session, club_id=club.id, skip=2, limit=2)
    assert len(hist_page2) == 1
    assert hist_page2[0].id == uvh1.id


async def test_delete_unit_value_history(db_session: AsyncSession):
    """Tests the internal deletion of a unit value history record."""
    club = await setup_basic_uvh_context(db_session)
    # Use helper which calls refactored CRUD
    created_uvh = await create_test_unit_value_history_via_crud(db_session, club)
    uvh_id = created_uvh.id

    # Test the delete CRUD function directly
    deleted_uvh = await crud_uvh.delete_unit_value_history(db=db_session, db_obj=created_uvh)
    assert deleted_uvh.id == uvh_id

    # Verify it's gone from DB
    retrieved = await crud_uvh.get_unit_value_history(db=db_session, unit_value_history_id=uvh_id)
    assert retrieved is None


async def test_create_duplicate_uvh_for_date_fails(db_session: AsyncSession):
    """Tests the database unique constraint (club_id, valuation_date)."""
    # Assumes unique constraint exists in DB model
    club = await setup_basic_uvh_context(db_session)
    v_date = date(2024, 6, 1)
    # Use the helper to create the first entry
    await create_test_unit_value_history_via_crud(db_session, club, valuation_date=v_date)

    # Try creating another entry for the same club and date by calling create directly
    uvh_data_dup = {
        "club_id": club.id,
        "valuation_date": v_date,
        # Provide valid values for other required fields
        "total_club_value": Decimal("11000.00"),
        "total_units_outstanding": Decimal("1000.00000000"),
        "unit_value": Decimal("11.00000000") # Calculated or explicit
    }
    with pytest.raises(IntegrityError):
        await crud_uvh.create_unit_value_history(db=db_session, uvh_data=uvh_data_dup)

