# backend/tests/crud/test_club_membership.py

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

# Import refactored CRUD function
from backend.crud import club_membership as crud_membership
from backend.models import Club, User, ClubMembership
from backend.models.enums import ClubRole
# Import only schemas needed for update
from backend.schemas import ClubMembershipUpdate # Removed ClubMembershipCreate

# Assuming helpers from test_user and test_club are available/imported
# Use the refactored club helper
from .test_user import create_test_user
from .test_club import create_test_club_via_crud # Use refactored helper

pytestmark = pytest.mark.asyncio(loop_scope="function")

# Helper function prepares data dict for refactored create_club_membership
async def create_test_membership_via_crud(
    db_session: AsyncSession, user: User, club: Club, role: ClubRole = ClubRole.MEMBER
) -> ClubMembership:
    """Helper prepares data dict and calls refactored create_club_membership."""
    # Check if membership already exists (e.g., creator in create_test_club)
    # Note: The refactored create_test_club_via_crud no longer creates the creator membership
    existing = await crud_membership.get_club_membership_by_user_and_club(
        db=db_session, user_id=user.id, club_id=club.id
    )
    if existing:
        # If it exists, potentially update its role if different? Or just return.
        # For simplicity, let's just return the existing one.
        # If role needs update, call update CRUD here.
        return existing

    membership_data = {
        "user_id": user.id,
        "club_id": club.id,
        "role": role,
    }
    return await crud_membership.create_club_membership(db=db_session, membership_data=membership_data)


async def test_create_club_membership(db_session: AsyncSession):
    # Fix: Remove invalid 'username' argument
    user = await create_test_user(db_session, email="member@example.com")
    creator = await create_test_user(db_session, email="creator_cm@example.com", auth0_sub="auth0|cm_creator")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)

    membership_role = ClubRole.MEMBER
    # Use the helper which calls the refactored CRUD
    created_membership = await create_test_membership_via_crud(
        db_session, user=user, club=club, role=membership_role
    )

    assert created_membership is not None
    assert created_membership.user_id == user.id
    assert created_membership.club_id == club.id
    assert created_membership.role == membership_role
    assert created_membership.id is not None


async def test_create_club_membership_default_role(db_session: AsyncSession):
    # Fix: Remove invalid 'username' argument
    user = await create_test_user(db_session, email="member2@example.com")
    creator = await create_test_user(db_session, email="creator_cm2@example.com", auth0_sub="auth0|cm_creator2")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)

    # Create without specifying role, should default to MEMBER (based on CRUD function)
    # Use the helper which calls the refactored CRUD
    created_membership = await create_test_membership_via_crud(
        db_session, user=user, club=club # Role defaults to MEMBER in helper/CRUD
    )
    assert created_membership.role == ClubRole.MEMBER


async def test_get_club_membership(db_session: AsyncSession):
    # Fix: Remove invalid 'username' argument
    user = await create_test_user(db_session, email="member3@example.com")
    creator = await create_test_user(db_session, email="creator_cm3@example.com", auth0_sub="auth0|cm_creator3")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Use the helper which calls the refactored CRUD
    created_membership = await create_test_membership_via_crud(db_session, user=user, club=club)

    retrieved_membership = await crud_membership.get_club_membership(
        db=db_session, membership_id=created_membership.id
    )

    assert retrieved_membership is not None
    assert retrieved_membership.id == created_membership.id
    assert retrieved_membership.user_id == user.id
    assert retrieved_membership.club_id == club.id


async def test_get_club_membership_not_found(db_session: AsyncSession):
    non_existent_id = uuid.uuid4()
    retrieved_membership = await crud_membership.get_club_membership(
        db=db_session, membership_id=non_existent_id
    )
    assert retrieved_membership is None


async def test_get_club_membership_by_user_and_club(db_session: AsyncSession):
    # Fix: Remove invalid 'username' argument
    user = await create_test_user(db_session, email="member4@example.com")
    creator = await create_test_user(db_session, email="creator_cm4@example.com", auth0_sub="auth0|cm_creator4")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Use the helper which calls the refactored CRUD
    created_membership = await create_test_membership_via_crud(db_session, user=user, club=club)

    retrieved_membership = await crud_membership.get_club_membership_by_user_and_club(
        db=db_session, user_id=user.id, club_id=club.id
    )

    assert retrieved_membership is not None
    assert retrieved_membership.id == created_membership.id


async def test_get_multi_club_memberships_by_club(db_session: AsyncSession):
    # Fix: Remove invalid 'username' argument
    creator = await create_test_user(db_session, email="creator_cm5@example.com", auth0_sub="auth0|cm_creator5")
    # Use refactored club helper (doesn't create creator membership)
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Fix: Remove invalid 'username' argument and provide unique auth0_sub
    user1 = await create_test_user(db_session, email="m1@example.com", auth0_sub="auth0|m1_sub") # Unique auth0_sub
    user2 = await create_test_user(db_session, email="m2@example.com", auth0_sub="auth0|m2_sub") # Unique auth0_sub
    # Use the helper which calls the refactored CRUD
    mem1 = await create_test_membership_via_crud(db_session, user=user1, club=club)
    mem2 = await create_test_membership_via_crud(db_session, user=user2, club=club)
    # Manually create creator's membership if needed for the test's logic
    creator_mem = await create_test_membership_via_crud(db_session, user=creator, club=club, role=ClubRole.ADMIN)


    memberships = await crud_membership.get_multi_club_memberships(
        db=db_session, club_id=club.id, limit=10
    )

    # Should now have 3 memberships (creator, user1, user2)
    assert len(memberships) == 3
    assert {m.id for m in memberships} == {creator_mem.id, mem1.id, mem2.id}


async def test_get_multi_club_memberships_by_user(db_session: AsyncSession):
    # Fix: Remove invalid 'username' argument
    user = await create_test_user(db_session, email="multi_club_user@example.com")
    creator1 = await create_test_user(db_session, email="c1@example.com", auth0_sub="auth0|c1")
    creator2 = await create_test_user(db_session, email="c2@example.com", auth0_sub="auth0|c2")
    # Use refactored club helper
    club1 = await create_test_club_via_crud(db_session, creator=creator1, name="Club X")
    club2 = await create_test_club_via_crud(db_session, creator=creator2, name="Club Y")
    # Use the helper which calls the refactored CRUD
    mem1 = await create_test_membership_via_crud(db_session, user=user, club=club1)
    mem2 = await create_test_membership_via_crud(db_session, user=user, club=club2)

    memberships = await crud_membership.get_multi_club_memberships(
        db=db_session, user_id=user.id, limit=10
    )

    assert len(memberships) == 2
    assert {m.id for m in memberships} == {mem1.id, mem2.id}


async def test_update_club_membership_role(db_session: AsyncSession):
    # Fix: Remove invalid 'username' argument
    user = await create_test_user(db_session, email="promote@example.com")
    creator = await create_test_user(db_session, email="creator_cm6@example.com", auth0_sub="auth0|cm_creator6")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Use the helper which calls the refactored CRUD
    membership = await create_test_membership_via_crud(db_session, user=user, club=club, role=ClubRole.MEMBER)

    assert membership.role == ClubRole.MEMBER

    update_data = ClubMembershipUpdate(role=ClubRole.ADMIN) # Changed role for test clarity
    updated_membership = await crud_membership.update_club_membership(
        db=db_session, db_obj=membership, obj_in=update_data
    )

    assert updated_membership is not None
    assert updated_membership.id == membership.id
    assert updated_membership.role == ClubRole.ADMIN

    # Verify in DB
    refetched = await crud_membership.get_club_membership(db=db_session, membership_id=membership.id)
    assert refetched.role == ClubRole.ADMIN


async def test_delete_club_membership(db_session: AsyncSession):
    # Fix: Remove invalid 'username' argument
    user = await create_test_user(db_session, email="delete@example.com")
    creator = await create_test_user(db_session, email="creator_cm7@example.com", auth0_sub="auth0|cm_creator7")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Use the helper which calls the refactored CRUD
    membership = await create_test_membership_via_crud(db_session, user=user, club=club)
    membership_id = membership.id

    deleted_membership = await crud_membership.delete_club_membership(
        db=db_session, db_obj=membership
    )
    assert deleted_membership.id == membership_id

    # Verify deletion
    retrieved = await crud_membership.get_club_membership(db=db_session, membership_id=membership_id)
    assert retrieved is None


async def test_create_duplicate_club_membership_fails(db_session: AsyncSession):
    # Fix: Remove invalid 'username' argument
    user = await create_test_user(db_session, email="dup_mem@example.com")
    creator = await create_test_user(db_session, email="creator_cm8@example.com", auth0_sub="auth0|cm_creator8")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Use the helper which calls the refactored CRUD for the first membership
    await create_test_membership_via_crud(db_session, user=user, club=club) # First membership

    # Fix: Try to create the same membership again by calling the CRUD function directly
    # This bypasses the check in the helper function.
    duplicate_membership_data = {
        "user_id": user.id,
        "club_id": club.id,
        "role": ClubRole.MEMBER, # Role doesn't matter for the constraint
    }
    with pytest.raises(IntegrityError): # Assumes unique constraint (user_id, club_id) exists
         await crud_membership.create_club_membership(db=db_session, membership_data=duplicate_membership_data)

