# backend/tests/api/test_clubs_api.py

import pytest
import pytest_asyncio
import uuid
from decimal import Decimal # Added for balance check
from typing import AsyncGenerator
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

# Import the FastAPI app instance
from backend.main import app

# Import schemas and models
from backend.schemas import (
    ClubCreate, ClubRead, ClubReadBasic, ClubMembershipRead,
    MemberAddSchema, MemberRoleUpdateSchema # Added membership schemas
)
from backend.models import User as UserModel, Club as ClubModel, Fund as FundModel, ClubMembership as MembershipModel, MemberTransaction as MemberTransactionModel
from backend.models.enums import ClubRole, MemberTransactionType

# Import CRUD functions for verification/setup
from backend.crud import club as crud_club
from backend.crud import fund as crud_fund
from backend.crud import club_membership as crud_membership
from backend.crud import user as crud_user
from backend.crud import member_transaction as crud_member_tx # Added member tx crud

# Import fixtures
# authenticated_user mocks get_current_active_user and provides the user object
from backend.tests.auth_fixtures import authenticated_user, test_user # Added test_user for creating non-authed users
# db_session provides a transactional database session
from backend.tests.conftest import db_session # Assuming db_session fixture is available

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio


# --- Test Fixture for API Client ---
@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an asynchronous test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

# --- Helper Function for Test Setup ---
async def create_club_with_membership(
    db: AsyncSession, user: UserModel, club_name: str, role: ClubRole = ClubRole.MEMBER
) -> tuple[ClubModel, MembershipModel]:
    """Helper to create a club and add a user as a member. Returns club and membership."""
    # Create a dummy creator for the club (can be the same user or another)
    creator = await crud_user.create_user(db, user_data={"email": f"creator_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|creator_{uuid.uuid4()}"})
    await db.flush()

    club = await crud_club.create_club(db, club_data={"name": club_name, "creator_id": creator.id})
    await db.flush()

    # Add the specified user as a member with the given role
    membership = await crud_membership.create_club_membership(db, membership_data={"user_id": user.id, "club_id": club.id, "role": role})
    await db.flush()
    await db.refresh(club) # Refresh to potentially load relationships if needed later
    await db.refresh(membership, attribute_names=['user', 'club']) # Refresh membership too
    return club, membership

# --- API Tests for POST /clubs ---

async def test_create_club_success(
    client: AsyncClient,
    db_session: AsyncSession, # Inject db_session for verification
    authenticated_user: UserModel # Mocks auth, provides creator user
):
    """
    Test successful club creation via POST /clubs.
    Verifies the club, default fund, and admin membership are created.
    """
    # Arrange
    club_name = f"Test API Club {uuid.uuid4().hex[:6]}"
    club_description = "Club created via API test"
    club_create_data = ClubCreate(name=club_name, description=club_description)
    creator = authenticated_user # The user performing the action

    # Act
    response = await client.post("/api/v1/clubs", json=club_create_data.model_dump())

    # Assert API Response
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()

    # Validate response schema
    created_club_response = ClubRead(**response_data)
    assert created_club_response.name == club_name
    assert created_club_response.description == club_description
    assert created_club_response.id is not None
    # Check if nested objects are present as expected by ClubRead schema
    assert len(created_club_response.funds) >= 1 # Should have at least the default fund
    assert any(f.name == "General Fund" for f in created_club_response.funds) # Check if default fund exists
    assert len(created_club_response.memberships) >= 1 # Should have at least the creator membership
    assert any(m.user_id == creator.id and m.role == ClubRole.ADMIN for m in created_club_response.memberships) # Check if creator admin exists

    # Assert Database State (Verify side effects)
    db_club = await crud_club.get_club(db=db_session, club_id=created_club_response.id)
    assert db_club is not None
    assert db_club.name == club_name
    assert db_club.creator_id == creator.id

    db_funds = await crud_fund.get_multi_funds(db=db_session, club_id=db_club.id)
    assert len(db_funds) >= 1
    assert any(f.name == "General Fund" for f in db_funds)

    db_membership = await crud_membership.get_club_membership_by_user_and_club(
        db=db_session, user_id=creator.id, club_id=db_club.id
    )
    assert db_membership is not None
    assert db_membership.role == ClubRole.ADMIN


async def test_create_club_unauthenticated(
    client: AsyncClient
):
    """
    Test POST /clubs endpoint without authentication.
    Expects a 401 Unauthorized error.
    """
    # Arrange
    club_create_data = ClubCreate(name="Unauthorized Club", description="")
    # Act
    response = await client.post("/api/v1/clubs", json=club_create_data.model_dump())
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- API Tests for GET /clubs ---

async def test_list_user_clubs_success(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel # Mocks auth, provides the user
):
    """
    Test GET /clubs returns clubs the authenticated user is a member of.
    """
    # Arrange: Create clubs and memberships
    user = authenticated_user
    club1, _ = await create_club_with_membership(db_session, user, "Club Alpha")
    club2, _ = await create_club_with_membership(db_session, user, "Club Beta", ClubRole.ADMIN)
    # Create a club the user is NOT a member of
    other_user = await crud_user.create_user(db_session, user_data={"email": f"other_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|other_{uuid.uuid4()}"})
    await db_session.flush()
    club_other, _ = await create_club_with_membership(db_session, other_user, "Club Gamma")

    expected_club_ids = {club1.id, club2.id}

    # Act
    response = await client.get("/api/v1/clubs")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data, list)
    retrieved_clubs = [ClubReadBasic(**item) for item in response_data]
    retrieved_club_ids = {club.id for club in retrieved_clubs}
    assert retrieved_club_ids == expected_club_ids
    assert len(retrieved_clubs) == 2
    assert retrieved_clubs[0].name == "Club Alpha"
    assert retrieved_clubs[1].name == "Club Beta"

async def test_list_user_clubs_unauthenticated(
    client: AsyncClient
):
    """
    Test GET /clubs endpoint without authentication.
    Expects a 401 Unauthorized error.
    """
    # Act
    response = await client.get("/api/v1/clubs")
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- API Tests for GET /clubs/{club_id} ---

async def test_get_single_club_success(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel # Mocks auth, provides the user
):
    """
    Test GET /clubs/{club_id} for a club the user is a member of.
    """
    # Arrange: Create a club where the authenticated user is a member
    user = authenticated_user
    club, _ = await create_club_with_membership(db_session, user, "Detailed Club")

    # Act
    response = await client.get(f"/api/v1/clubs/{club.id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    club_details = ClubRead(**response_data)
    assert club_details.id == club.id
    assert club_details.name == club.name
    assert isinstance(club_details.memberships, list)
    assert isinstance(club_details.funds, list)
    assert any(m.user_id == user.id for m in club_details.memberships)

async def test_get_single_club_not_found(
    client: AsyncClient,
    authenticated_user: UserModel # Need auth to pass the dependency check initially
):
    """
    Test GET /clubs/{club_id} for a non-existent club ID.
    """
    # Arrange
    non_existent_club_id = uuid.uuid4()
    # Act
    response = await client.get(f"/api/v1/clubs/{non_existent_club_id}")
    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND

async def test_get_single_club_unauthenticated(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: UserModel # Use test_user fixture to create a user without mocking auth
):
    """
    Test GET /clubs/{club_id} without authentication.
    """
    # Arrange: Create a club, but don't authenticate the request
    club, _ = await create_club_with_membership(db_session, test_user, "Auth Test Club")
    # Act
    response = await client.get(f"/api/v1/clubs/{club.id}")
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_get_single_club_not_member(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel # Mocks auth for User A
):
    """
    Test GET /clubs/{club_id} for a club the authenticated user is NOT a member of.
    Expects 403 Forbidden.
    """
    # Arrange:
    user_a = authenticated_user
    user_b = await crud_user.create_user(db_session, user_data={"email": f"user_b_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|user_b_{uuid.uuid4()}"})
    await db_session.flush()
    club_b, _ = await create_club_with_membership(db_session, user_b, "User B's Club")

    # Act: User A tries to access User B's club details
    response = await client.get(f"/api/v1/clubs/{club_b.id}")

    # Assert:
    assert response.status_code == status.HTTP_403_FORBIDDEN

# --- API Tests for Club Membership Management ---

@pytest_asyncio.fixture(scope="function")
async def club_admin_user(db_session: AsyncSession) -> UserModel:
    """Fixture to create an admin user for testing."""
    user = await crud_user.create_user(db_session, user_data={"email": f"admin_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|admin_{uuid.uuid4()}"})
    await db_session.flush()
    return user

@pytest_asyncio.fixture(scope="function")
async def club_member_user(db_session: AsyncSession) -> UserModel:
    """Fixture to create a regular member user for testing."""
    user = await crud_user.create_user(db_session, user_data={"email": f"member_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|member_{uuid.uuid4()}"})
    await db_session.flush()
    return user

@pytest_asyncio.fixture(scope="function")
async def club_with_admin_and_member(db_session: AsyncSession, club_admin_user: UserModel, club_member_user: UserModel) -> tuple[ClubModel, UserModel, UserModel]:
    """Fixture to create a club with an admin and a regular member."""
    club, admin_membership = await create_club_with_membership(db_session, club_admin_user, "Membership Test Club", ClubRole.ADMIN)
    _, member_membership = await create_club_with_membership(db_session, club_member_user, club.name, ClubRole.MEMBER) # Add member to same club
    return club, club_admin_user, club_member_user

# --- GET /clubs/{club_id}/members ---

async def test_list_members_success(
    client: AsyncClient,
    db_session: AsyncSession,
    authenticated_user: UserModel, # Mocks auth for the requesting user
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
):
    """Test listing members as an authenticated member."""
    club, admin_user, member_user = club_with_admin_and_member
    requesting_user = admin_user # Test as admin first

    # Mock authentication to be the admin user
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: requesting_user)

        # Act
        response = await client.get(f"/api/v1/clubs/{club.id}/members")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert isinstance(response_data, list)
        memberships = [ClubMembershipRead(**item) for item in response_data]

        assert len(memberships) == 2 # Admin + Member
        member_user_ids = {m.user_id for m in memberships}
        assert admin_user.id in member_user_ids
        assert member_user.id in member_user_ids

async def test_list_members_unauthenticated(client: AsyncClient, club_with_admin_and_member):
    """Test listing members without authentication."""
    club, _, _ = club_with_admin_and_member
    response = await client.get(f"/api/v1/clubs/{club.id}/members")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_list_members_not_member(client: AsyncClient, db_session: AsyncSession, authenticated_user: UserModel, club_with_admin_and_member):
    """Test listing members of a club the user is not part of."""
    club, _, _ = club_with_admin_and_member
    # Create a user who is authenticated but not in club_with_admin_and_member
    non_member_user = await crud_user.create_user(db_session, user_data={"email": f"nonmember_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|nonmember_{uuid.uuid4()}"})
    await db_session.flush()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: non_member_user)
        response = await client.get(f"/api/v1/clubs/{club.id}/members")
        assert response.status_code == status.HTTP_403_FORBIDDEN

# --- POST /clubs/{club_id}/members ---

async def test_add_member_success_by_admin(
    client: AsyncClient,
    db_session: AsyncSession,
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
):
    """Test adding a new member by an admin."""
    club, admin_user, _ = club_with_admin_and_member
    # Create a new user to add
    new_user_to_add = await crud_user.create_user(db_session, user_data={"email": f"newbie_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|newbie_{uuid.uuid4()}"})
    await db_session.flush()

    add_data = MemberAddSchema(member_email=new_user_to_add.email, role=ClubRole.MEMBER)

    # Mock authentication as the admin user
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)

        # Act
        response = await client.post(f"/api/v1/clubs/{club.id}/members", json=add_data.model_dump())

        # Assert API Response
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        new_membership = ClubMembershipRead(**response_data)
        assert new_membership.club_id == club.id
        assert new_membership.user_id == new_user_to_add.id
        assert new_membership.role == ClubRole.MEMBER

        # Assert Database State
        db_membership = await crud_membership.get_club_membership_by_user_and_club(
            db=db_session, user_id=new_user_to_add.id, club_id=club.id
        )
        assert db_membership is not None
        assert db_membership.role == ClubRole.MEMBER

async def test_add_member_forbidden_by_member(
    client: AsyncClient,
    db_session: AsyncSession,
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
):
    """Test adding a member fails when attempted by a non-admin member."""
    club, _, member_user = club_with_admin_and_member
    new_user_to_add = await crud_user.create_user(db_session, user_data={"email": f"newbie2_{uuid.uuid4()}@test.com", "auth0_sub": f"auth0|newbie2_{uuid.uuid4()}"})
    await db_session.flush()
    add_data = MemberAddSchema(member_email=new_user_to_add.email)

    # Mock authentication as the regular member user
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user)
        response = await client.post(f"/api/v1/clubs/{club.id}/members", json=add_data.model_dump())
        assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_add_member_already_exists(
    client: AsyncClient,
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
):
    """Test adding a member who is already in the club."""
    club, admin_user, member_user = club_with_admin_and_member
    add_data = MemberAddSchema(member_email=member_user.email) # Try to add existing member

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        response = await client.post(f"/api/v1/clubs/{club.id}/members", json=add_data.model_dump())
        assert response.status_code == status.HTTP_409_CONFLICT

async def test_add_member_user_not_found(
    client: AsyncClient,
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
):
    """Test adding a member whose email doesn't exist in the system."""
    club, admin_user, _ = club_with_admin_and_member
    add_data = MemberAddSchema(member_email="nosuchuser@example.com")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        response = await client.post(f"/api/v1/clubs/{club.id}/members", json=add_data.model_dump())
        assert response.status_code == status.HTTP_404_NOT_FOUND

# --- PUT /clubs/{club_id}/members/{user_id} ---

async def test_update_member_role_success_by_admin(
    client: AsyncClient,
    db_session: AsyncSession,
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
):
    """Test updating a member's role to ADMIN by an admin."""
    club, admin_user, member_user = club_with_admin_and_member
    update_data = MemberRoleUpdateSchema(new_role=ClubRole.ADMIN)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        response = await client.put(f"/api/v1/clubs/{club.id}/members/{member_user.id}", json=update_data.model_dump())

        # Assert API Response
        assert response.status_code == status.HTTP_200_OK
        updated_membership = ClubMembershipRead(**response.json())
        assert updated_membership.user_id == member_user.id
        assert updated_membership.role == ClubRole.ADMIN

        # Assert Database State
        db_membership = await crud_membership.get_club_membership_by_user_and_club(db_session, user_id=member_user.id, club_id=club.id)
        assert db_membership.role == ClubRole.ADMIN

async def test_update_member_role_forbidden_by_member(
    client: AsyncClient,
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
):
    """Test updating a role fails when attempted by a non-admin member."""
    club, admin_user, member_user = club_with_admin_and_member
    update_data = MemberRoleUpdateSchema(new_role=ClubRole.ADMIN)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user) # Authenticate as member
        response = await client.put(f"/api/v1/clubs/{club.id}/members/{admin_user.id}", json=update_data.model_dump()) # Try to change admin's role
        assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_update_member_role_last_admin(
    client: AsyncClient,
    db_session: AsyncSession,
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
):
    """Test preventing the removal of the last admin role."""
    club, admin_user, member_user = club_with_admin_and_member
    # Demote the regular member first (or remove them) so only admin_user is ADMIN
    await crud_membership.delete_club_membership(db_session, db_obj=(await crud_membership.get_club_membership_by_user_and_club(db_session, user_id=member_user.id, club_id=club.id)))
    await db_session.flush()

    update_data = MemberRoleUpdateSchema(new_role=ClubRole.MEMBER) # Try to demote the last admin

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user) # Authenticate as admin
        response = await client.put(f"/api/v1/clubs/{club.id}/members/{admin_user.id}", json=update_data.model_dump())
        assert response.status_code == status.HTTP_400_BAD_REQUEST # Service should prevent this

# --- DELETE /clubs/{club_id}/members/{user_id} ---

async def test_remove_member_success_by_admin(
    client: AsyncClient,
    db_session: AsyncSession,
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
):
    """Test removing a member (with zero balance) by an admin."""
    club, admin_user, member_user = club_with_admin_and_member
    member_to_remove_id = member_user.id # ID of the user being removed

    # Ensure member has zero balance (no transactions created yet)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        response = await client.delete(f"/api/v1/clubs/{club.id}/members/{member_to_remove_id}")

        # Assert API Response
        assert response.status_code == status.HTTP_200_OK
        deleted_membership = ClubMembershipRead(**response.json())
        assert deleted_membership.user_id == member_to_remove_id
        assert deleted_membership.club_id == club.id

        # Assert Database State
        db_membership = await crud_membership.get_club_membership_by_user_and_club(db_session, user_id=member_to_remove_id, club_id=club.id)
        assert db_membership is None

async def test_remove_member_forbidden_by_member(
    client: AsyncClient,
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
):
    """Test removing a member fails when attempted by a non-admin."""
    club, admin_user, member_user = club_with_admin_and_member

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: member_user) # Authenticate as member
        response = await client.delete(f"/api/v1/clubs/{club.id}/members/{admin_user.id}") # Try to remove admin
        assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_remove_member_last_admin(
    client: AsyncClient,
    db_session: AsyncSession,
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
):
    """Test preventing removal of the last admin."""
    club, admin_user, member_user = club_with_admin_and_member
    # Remove the regular member so only admin_user is left as ADMIN
    member_membership = await crud_membership.get_club_membership_by_user_and_club(db_session, user_id=member_user.id, club_id=club.id)
    await crud_membership.delete_club_membership(db_session, db_obj=member_membership)
    await db_session.flush()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user) # Authenticate as admin
        response = await client.delete(f"/api/v1/clubs/{club.id}/members/{admin_user.id}") # Try to remove self (last admin)
        # Should be blocked by service layer logic (prevent self-removal or last admin removal)
        assert response.status_code == status.HTTP_403_FORBIDDEN # Or 400 depending on service logic

async def test_remove_member_with_balance(
    client: AsyncClient,
    db_session: AsyncSession,
    club_with_admin_and_member: tuple[ClubModel, UserModel, UserModel]
):
    """Test preventing removal of a member with a non-zero unit balance."""
    club, admin_user, member_user = club_with_admin_and_member
    member_membership = await crud_membership.get_club_membership_by_user_and_club(db_session, user_id=member_user.id, club_id=club.id)

    # Give the member a balance by creating a deposit transaction
    await crud_member_tx.create_member_transaction(
        db_session,
        member_tx_data={
            "membership_id": member_membership.id,
            "transaction_type": MemberTransactionType.DEPOSIT,
            "amount": Decimal("100.00"),
            "unit_value_used": Decimal("10.0"),
            "units_transacted": Decimal("10.0")
        }
    )
    await db_session.flush()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.api.dependencies.get_current_active_user", lambda: admin_user)
        response = await client.delete(f"/api/v1/clubs/{club.id}/members/{member_user.id}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "unit balance is" in response.json()["detail"]


