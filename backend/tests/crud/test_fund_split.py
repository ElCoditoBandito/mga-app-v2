# backend/tests/crud/test_fund_split.py

import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select # Import select for helper check
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Import refactored CRUD function
from backend.crud import fund_split as crud_split
# Import models needed
from backend.models import Club, User, Fund, ClubMembership, FundSplit # Keep models
# Import only schemas needed for update
from backend.schemas import FundSplitUpdate # Removed FundSplitCreate

# Import refactored helpers
from .test_user import create_test_user
from .test_club import create_test_club_via_crud
# from .test_club_membership import create_test_membership_via_crud # No longer needed directly for split creation
from .test_fund import create_test_fund_via_crud # Use refactored helper

pytestmark = pytest.mark.asyncio(loop_scope="function")

# Helper prepares data dict for refactored create_fund_split (Club Level)
async def create_test_fund_split_via_crud(
    db_session: AsyncSession, club: Club, fund: Fund, percentage: Decimal = Decimal("1.0000") # Assuming percentage 0-1
) -> FundSplit:
    """Helper prepares data dict and calls refactored create_fund_split."""
    # Check if split already exists for this club/fund
    existing_split_result = await db_session.execute(
        select(FundSplit).filter_by(club_id=club.id, fund_id=fund.id)
    )
    existing_split = existing_split_result.scalars().first()
    if existing_split:
         return existing_split # Return existing to avoid setup failures

    # Use 'split_percentage' matching the model field name
    fund_split_data = {
        "club_id": club.id, # Use club_id
        "fund_id": fund.id,
        "split_percentage": percentage,
    }
    return await crud_split.create_fund_split(db=db_session, fund_split_data=fund_split_data)


# Helper to setup club and fund context
async def setup_basic_split_context(db_session: AsyncSession):
    # Ensure unique users/creators
    creator = await create_test_user(db_session, email=f"splitcreator_{uuid.uuid4()}@example.com", auth0_sub=f"auth0|split_cr_{uuid.uuid4()}")
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Create a fund explicitly
    fund = await create_test_fund_via_crud(db_session, club=club, name="Split Test Fund")
    return club, fund # Return only club and fund


async def test_create_fund_split(db_session: AsyncSession):
    club, fund = await setup_basic_split_context(db_session)
    percentage = Decimal("1.0000") # e.g., 100%
    # Use helper which calls refactored CRUD
    created_split = await create_test_fund_split_via_crud(db_session, club, fund, percentage=percentage)

    assert created_split is not None
    assert created_split.club_id == club.id
    assert created_split.fund_id == fund.id
    # Check correct attribute name based on model definition ('split_percentage')
    assert created_split.split_percentage == percentage
    assert created_split.id is not None
    # assert created_split.membership_id is None # No longer exists


async def test_get_fund_split(db_session: AsyncSession):
    club, fund = await setup_basic_split_context(db_session)
    # Use helper which calls refactored CRUD
    created_split = await create_test_fund_split_via_crud(db_session, club, fund)

    retrieved_split = await crud_split.get_fund_split(db=db_session, fund_split_id=created_split.id)

    assert retrieved_split is not None
    assert retrieved_split.id == created_split.id
    assert retrieved_split.club_id == club.id
    assert retrieved_split.fund_id == fund.id


async def test_get_fund_split_not_found(db_session: AsyncSession):
    non_existent_id = uuid.uuid4()
    retrieved_split = await crud_split.get_fund_split(db=db_session, fund_split_id=non_existent_id)
    assert retrieved_split is None

# Test for getting splits by membership is no longer relevant

async def test_get_fund_splits_by_club(db_session: AsyncSession): # Renamed test
    club, fund1 = await setup_basic_split_context(db_session)
    # Create a second fund using helper
    fund2 = await create_test_fund_via_crud(db_session, club=club, name="Second Fund")

    # Create two splits for the same club into different funds using helper
    split1 = await create_test_fund_split_via_crud(db_session, club, fund1, percentage=Decimal("0.6000"))
    split2 = await create_test_fund_split_via_crud(db_session, club, fund2, percentage=Decimal("0.4000"))

    # Create another club and split to ensure filtering works
    creator2 = await create_test_user(db_session, email=f"other_{uuid.uuid4()}@s.com", auth0_sub=f"auth0|othersplit_{uuid.uuid4()}")
    club2 = await create_test_club_via_crud(db_session, creator=creator2, name="Other Split Club")
    fund3 = await create_test_fund_via_crud(db_session, club=club2, name="Gamma Fund")
    await create_test_fund_split_via_crud(db_session, club2, fund3, percentage=Decimal("1.0000"))


    splits = await crud_split.get_fund_splits_by_club(db=db_session, club_id=club.id) # Use new getter

    assert len(splits) == 2
    assert {s.id for s in splits} == {split1.id, split2.id}


async def test_get_fund_splits_by_fund(db_session: AsyncSession):
    # Setup two clubs
    creator1 = await create_test_user(db_session, email=f"splitcreator1_{uuid.uuid4()}@example.com", auth0_sub=f"auth0|split_cr1_{uuid.uuid4()}")
    club1 = await create_test_club_via_crud(db_session, creator=creator1, name="Split Club A")
    creator2 = await create_test_user(db_session, email=f"splitcreator2_{uuid.uuid4()}@example.com", auth0_sub=f"auth0|split_cr2_{uuid.uuid4()}")
    club2 = await create_test_club_via_crud(db_session, creator=creator2, name="Split Club B")

    # Create one fund used by both clubs
    fund_shared = await create_test_fund_via_crud(db_session, club=club1, name="Shared Fund")
    # Need to ensure fund can exist without splits or handle creation carefully if linked back

    # Create splits for the shared fund in both clubs
    split1 = await create_test_fund_split_via_crud(db_session, club1, fund_shared, percentage=Decimal("0.5000"))
    split2 = await create_test_fund_split_via_crud(db_session, club2, fund_shared, percentage=Decimal("1.0000"))

    # Get splits for the specific fund
    splits_for_fund = await crud_split.get_fund_splits_by_fund(db=db_session, fund_id=fund_shared.id)

    # Should get splits from both clubs for this fund
    assert len(splits_for_fund) == 2
    assert {s.id for s in splits_for_fund} == {split1.id, split2.id}


async def test_update_fund_split(db_session: AsyncSession):
    club, fund = await setup_basic_split_context(db_session)
    # Use helper
    created_split = await create_test_fund_split_via_crud(db_session, club, fund, percentage=Decimal("1.0000"))

    new_percentage = Decimal("0.7550")
    # Update schema likely only takes percentage - check its definition
    # Use 'split_percentage' if that's the field name in the schema
    update_data = FundSplitUpdate(split_percentage=new_percentage)
    updated_split = await crud_split.update_fund_split(
        db=db_session, db_obj=created_split, obj_in=update_data
    )

    assert updated_split is not None
    assert updated_split.id == created_split.id
    # Check correct attribute name based on model definition
    assert updated_split.split_percentage == new_percentage

    refetched = await crud_split.get_fund_split(db=db_session, fund_split_id=created_split.id)
    # Check correct attribute name based on model definition
    assert refetched.split_percentage == new_percentage


async def test_delete_fund_split(db_session: AsyncSession):
    club, fund = await setup_basic_split_context(db_session)
    # Use helper
    created_split = await create_test_fund_split_via_crud(db_session, club, fund)
    split_id = created_split.id

    deleted_split = await crud_split.delete_fund_split(db=db_session, db_obj=created_split)
    assert deleted_split.id == split_id

    retrieved = await crud_split.get_fund_split(db=db_session, fund_split_id=split_id)
    assert retrieved is None


async def test_create_duplicate_fund_split_fails(db_session: AsyncSession):
    # Constraint is now on (club_id, fund_id)
    club, fund = await setup_basic_split_context(db_session)
    # Use helper for first split
    await create_test_fund_split_via_crud(db_session, club, fund, percentage=Decimal("1.0000"))

    # Try creating another split for the same club and fund by calling CRUD directly
    fund_split_data_dup = {
        "club_id": club.id,
        "fund_id": fund.id,
        "split_percentage": Decimal("0.5000")
    }
    with pytest.raises(IntegrityError):
        await crud_split.create_fund_split(db=db_session, fund_split_data=fund_split_data_dup)

