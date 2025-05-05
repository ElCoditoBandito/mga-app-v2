# backend/tests/crud/test_club.py

import uuid
# from typing import AsyncGenerator # No longer needed

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Import refactored CRUD function
from backend.crud import club as crud_club
# Import models needed
from backend.models import Club, User
# Import schemas needed for update
from backend.schemas import ClubUpdate # Removed ClubCreate

# Make imports from test_user available
from .test_user import create_test_user # Assuming helper exists

pytestmark = pytest.mark.asyncio(loop_scope="function")

# Helper function now prepares data dict for refactored create_club
async def create_test_club_via_crud(
    db_session: AsyncSession, creator: User, name: str = "Test Club", description: str = "A club for testing"
) -> Club:
    """Helper prepares data dict and calls refactored create_club."""
    club_data = {
        "name": name,
        "description": description,
        "creator_id": creator.id, # Pass creator_id directly
        # Add other fields if needed by Club model, e.g., bank_account_balance
    }
    return await crud_club.create_club(db=db_session, club_data=club_data)


async def test_create_club(db_session: AsyncSession):
    creator = await create_test_user(db_session)
    club_name = "The Founders Club"
    club_description = "First club created"

    # Use the helper which calls the refactored CRUD
    created_club = await create_test_club_via_crud(
        db_session, creator=creator, name=club_name, description=club_description
    )

    # Assert only the Club object properties
    assert created_club is not None
    assert created_club.name == club_name
    assert created_club.description == club_description
    assert created_club.creator_id == creator.id # Check creator_id was set
    assert created_club.id is not None

    # --- REMOVED ---
    # The refactored CRUD function no longer creates default fund or membership.
    # These checks belong in a Service layer test.
    # Verify default fund creation
    # default_fund = await crud_club.get_default_fund_for_club(db=db_session, club_id=created_club.id)
    # assert default_fund is not None
    # Verify creator membership and role
    # membership = await crud_membership.get_club_membership_by_user_and_club(...)
    # assert membership is not None
    # assert membership.role == ClubRole.ADMIN
    # --- END REMOVED ---


async def test_get_club(db_session: AsyncSession):
    creator = await create_test_user(db_session)
    # Use the helper
    created_club = await create_test_club_via_crud(db_session, creator=creator)

    retrieved_club = await crud_club.get_club(db=db_session, club_id=created_club.id)

    assert retrieved_club is not None
    assert retrieved_club.id == created_club.id
    assert retrieved_club.name == created_club.name


async def test_get_club_not_found(db_session: AsyncSession):
    non_existent_id = uuid.uuid4()
    retrieved_club = await crud_club.get_club(db=db_session, club_id=non_existent_id)
    assert retrieved_club is None


async def test_get_club_by_name(db_session: AsyncSession):
    creator = await create_test_user(db_session)
    club_name = "Unique Club Name Alpha"
    # Use the helper
    created_club = await create_test_club_via_crud(db_session, creator=creator, name=club_name)

    retrieved_club = await crud_club.get_club_by_name(db=db_session, name=club_name)

    assert retrieved_club is not None
    assert retrieved_club.id == created_club.id
    assert retrieved_club.name == club_name


async def test_get_club_by_name_not_found(db_session: AsyncSession):
    retrieved_club = await crud_club.get_club_by_name(db=db_session, name="NoSuchClub")
    assert retrieved_club is None


async def test_get_multi_clubs(db_session: AsyncSession):
    creator = await create_test_user(db_session)
    # Use the helper
    club1 = await create_test_club_via_crud(db_session, creator=creator, name="Club B")
    club2 = await create_test_club_via_crud(db_session, creator=creator, name="Club A")
    club3 = await create_test_club_via_crud(db_session, creator=creator, name="Club C")

    # Test default pagination
    clubs_page1 = await crud_club.get_multi_clubs(db=db_session, skip=0, limit=2)
    assert len(clubs_page1) == 2
    # Note: Order is by name, then id. Here, names are unique.
    assert {c.id for c in clubs_page1} == {club2.id, club1.id} # Club A, Club B

    # Test skipping
    clubs_page2 = await crud_club.get_multi_clubs(db=db_session, skip=1, limit=2)
    assert len(clubs_page2) == 2
    assert {c.id for c in clubs_page2} == {club1.id, club3.id} # Club B, Club C

    # Test limit larger than available
    clubs_all = await crud_club.get_multi_clubs(db=db_session, skip=0, limit=10)
    assert len(clubs_all) == 3
    assert {c.id for c in clubs_all} == {club1.id, club2.id, club3.id}


async def test_update_club(db_session: AsyncSession):
    creator = await create_test_user(db_session)
    # Use the helper
    created_club = await create_test_club_via_crud(db_session, creator=creator)

    update_data = ClubUpdate(description="Updated description")
    updated_club = await crud_club.update_club(
        db=db_session, db_obj=created_club, obj_in=update_data
    )

    assert updated_club is not None
    assert updated_club.id == created_club.id
    assert updated_club.name == created_club.name # Name not updated
    assert updated_club.description == "Updated description"

    # Verify in DB
    refetched_club = await crud_club.get_club(db=db_session, club_id=created_club.id)
    assert refetched_club.description == "Updated description"


async def test_update_club_partial(db_session: AsyncSession):
    creator = await create_test_user(db_session)
    # Use the helper
    created_club = await create_test_club_via_crud(db_session, creator=creator, name="Original Name")

    # Only update description, name should remain unchanged
    update_data = ClubUpdate(description="New Description Only")
    updated_club = await crud_club.update_club(
        db=db_session, db_obj=created_club, obj_in=update_data
    )

    assert updated_club.name == "Original Name"
    assert updated_club.description == "New Description Only"


async def test_delete_club(db_session: AsyncSession):
    # Note: This test might change significantly depending on cascade behavior
    # and whether related objects (funds, memberships) should be manually
    # created for a more isolated test of Club deletion.
    # For now, assume cascade delete works or no related objects block deletion.
    creator = await create_test_user(db_session)
    # Use the helper
    created_club = await create_test_club_via_crud(db_session, creator=creator)
    club_id = created_club.id

    # --- REMOVED ---
    # Default fund/membership are no longer created by the CRUD helper
    # default_fund = await crud_club.get_default_fund_for_club(...)
    # creator_membership = await crud_membership.get_club_membership_by_user_and_club(...)
    # --- END REMOVED ---

    deleted_club = await crud_club.delete_club(db=db_session, db_obj=created_club)
    assert deleted_club.id == club_id

    # Verify club is deleted
    retrieved_club = await crud_club.get_club(db=db_session, club_id=club_id)
    assert retrieved_club is None

    # --- REMOVED ---
    # Cannot verify deletion of objects not created in this test's scope
    # retrieved_fund = await crud_fund.get_fund(...)
    # assert retrieved_fund is None, "Default fund should be deleted by cascade"
    # retrieved_membership = await crud_membership.get_club_membership(...)
    # assert retrieved_membership is None, "Creator membership should be deleted by cascade"
    # --- END REMOVED ---


# Example: Add a unique constraint test if Club.name should be unique
# (Assuming UNIQUE constraint is on Club.name in the model)
# async def test_create_club_duplicate_name_fails(db_session: AsyncSession):
#     creator = await create_test_user(db_session)
#     club_name = "Duplicate Name Club"
#     await create_test_club_via_crud(db_session, creator=creator, name=club_name)
#
#     creator2 = await create_test_user(db_session, email="test2@example.com", username="testuser2")
#
#     # Prepare data dict for refactored function
#     club_data_dup = {
#         "name": club_name,
#         "description": "Trying duplicate",
#         "creator_id": creator2.id
#     }
#     with pytest.raises(IntegrityError):
#         await crud_club.create_club(db=db_session, club_data=club_data_dup)

