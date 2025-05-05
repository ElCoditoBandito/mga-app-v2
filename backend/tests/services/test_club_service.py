# backend/tests/services/test_club_service.py

import pytest
import uuid
from decimal import Decimal
from unittest.mock import patch, AsyncMock, call # Import mocking utilities

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError # For testing error handling
from fastapi import HTTPException

# Service functions to test
from backend.services import club_service
# CRUD functions will be mocked
# Models and Schemas for type hinting and input/output definition
from backend.models import User, Club, Fund, ClubMembership
from backend.models.enums import ClubRole
from backend.schemas import ClubCreate, ClubMembershipUpdate

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio

# --- Test Data ---
TEST_USER_ID = uuid.uuid4()
TEST_ADMIN_ID = uuid.uuid4()
TEST_MEMBER_ID = uuid.uuid4()
TEST_CLUB_ID = uuid.uuid4()
TEST_FUND_ID = uuid.uuid4()
TEST_MEMBERSHIP_ID = uuid.uuid4()

# --- Tests for create_club ---

# Patch all CRUD functions called within club_service.create_club
@patch('backend.services.club_service.crud_user.get_user_by_auth0_sub', new_callable=AsyncMock)
@patch('backend.services.club_service.crud_club.create_club', new_callable=AsyncMock)
@patch('backend.services.club_service.crud_fund.create_fund', new_callable=AsyncMock)
@patch('backend.services.club_service.crud_membership.create_club_membership', new_callable=AsyncMock)
async def test_create_club_success(
    mock_create_membership: AsyncMock,
    mock_create_fund: AsyncMock,
    mock_create_club: AsyncMock,
    mock_get_user: AsyncMock,
    db_session: AsyncSession
):
    """ Test successful club creation including default fund and admin membership. """
    # Arrange
    creator_auth0_sub = f"auth0|create_{uuid.uuid4().hex[:6]}"
    creator_email = f"create_{uuid.uuid4().hex[:6]}@svc.test"
    club_name = "Club Alpha"
    club_in = ClubCreate(name=club_name, description="Testing creation")

    # Mock finding the creator user
    mock_creator = User(id=TEST_USER_ID, auth0_sub=creator_auth0_sub, email=creator_email, is_active=True)
    mock_get_user.return_value = mock_creator

    # Mock the results of the creation CRUD calls
    mock_club = Club(id=TEST_CLUB_ID, name=club_name, description=club_in.description, creator_id=TEST_USER_ID)
    mock_fund = Fund(id=TEST_FUND_ID, club_id=TEST_CLUB_ID, name="General Fund")
    mock_membership = ClubMembership(id=TEST_MEMBERSHIP_ID, user_id=TEST_USER_ID, club_id=TEST_CLUB_ID, role=ClubRole.ADMIN)

    mock_create_club.return_value = mock_club
    mock_create_fund.return_value = mock_fund
    mock_create_membership.return_value = mock_membership

    # Expected data passed to CRUD functions
    expected_club_data = {"name": club_name, "description": club_in.description, "creator_id": TEST_USER_ID}
    expected_fund_data = {"club_id": TEST_CLUB_ID, "name": "General Fund", "description": "Default fund for general club holdings.", "is_active": True}
    expected_membership_data = {"user_id": TEST_USER_ID, "club_id": TEST_CLUB_ID, "role": ClubRole.ADMIN}

    # Act
    created_club_result = await club_service.create_club(db=db_session, club_in=club_in, auth0_sub=creator_auth0_sub)

    # Assert
    mock_get_user.assert_called_once_with(db=db_session, auth0_sub=creator_auth0_sub)
    mock_create_club.assert_called_once_with(db=db_session, club_data=expected_club_data)
    mock_create_fund.assert_called_once_with(db=db_session, fund_data=expected_fund_data)
    mock_create_membership.assert_called_once_with(db=db_session, membership_data=expected_membership_data)
    assert created_club_result == mock_club # Service should return the created club object

@patch('backend.services.club_service.crud_user.get_user_by_auth0_sub', new_callable=AsyncMock)
async def test_create_club_user_not_found(mock_get_user: AsyncMock, db_session: AsyncSession):
    """ Test club creation fails if the requesting user doesn't exist. """
    # Arrange
    non_existent_auth0_sub = "auth0|no_such_user"
    club_in = ClubCreate(name="Wont Be Created", description="")
    mock_get_user.return_value = None # Simulate user not found

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await club_service.create_club(db=db_session, club_in=club_in, auth0_sub=non_existent_auth0_sub)

    assert exc_info.value.status_code == 404
    assert f"User with auth0_sub '{non_existent_auth0_sub}' not found" in exc_info.value.detail
    mock_get_user.assert_called_once_with(db=db_session, auth0_sub=non_existent_auth0_sub)

# --- Tests for get_club_details ---

@patch('backend.services.club_service.crud_club.get_club', new_callable=AsyncMock)
async def test_get_club_details_found(mock_get_club: AsyncMock, db_session: AsyncSession):
    """ Test retrieving details for an existing club. """
    # Arrange
    club_id = uuid.uuid4()
    expected_club = Club(id=club_id, name="Found Club")
    mock_get_club.return_value = expected_club

    # Act
    fetched_club = await club_service.get_club_details(db=db_session, club_id=club_id)

    # Assert
    mock_get_club.assert_called_once_with(db=db_session, club_id=club_id)
    assert fetched_club == expected_club

@patch('backend.services.club_service.crud_club.get_club', new_callable=AsyncMock)
async def test_get_club_details_not_found(mock_get_club: AsyncMock, db_session: AsyncSession):
    """ Test retrieving details for a non-existent club. """
    # Arrange
    club_id = uuid.uuid4()
    mock_get_club.return_value = None # Simulate not found

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await club_service.get_club_details(db=db_session, club_id=club_id)

    assert exc_info.value.status_code == 404
    assert f"Club with id {club_id} not found" in exc_info.value.detail
    mock_get_club.assert_called_once_with(db=db_session, club_id=club_id)


# --- Tests for list_user_clubs --- (Illustrative Example)

@patch('backend.services.club_service.crud_user.get_user_by_auth0_sub', new_callable=AsyncMock)
@patch('backend.services.club_service.crud_membership.get_multi_club_memberships', new_callable=AsyncMock)
async def test_list_user_clubs_multiple(mock_get_memberships: AsyncMock, mock_get_user: AsyncMock, db_session: AsyncSession):
    """ Test listing multiple clubs for a single user. """
    # Arrange
    user_auth0_sub = f"auth0|list_{uuid.uuid4().hex[:6]}"
    mock_user = User(id=TEST_USER_ID, auth0_sub=user_auth0_sub, email="list@t.com")
    mock_get_user.return_value = mock_user

    # Simulate memberships returned by CRUD
    club1 = Club(id=uuid.uuid4(), name="Club A")
    club2 = Club(id=uuid.uuid4(), name="Club B")
    mock_memberships = [
        ClubMembership(id=uuid.uuid4(), user_id=TEST_USER_ID, club_id=club1.id, role=ClubRole.MEMBER, club=club1),
        ClubMembership(id=uuid.uuid4(), user_id=TEST_USER_ID, club_id=club2.id, role=ClubRole.ADMIN, club=club2),
    ]
    mock_get_memberships.return_value = mock_memberships

    # Act
    user_clubs = await club_service.list_user_clubs(db=db_session, auth0_sub=user_auth0_sub)

    # Assert
    mock_get_user.assert_called_once_with(db=db_session, auth0_sub=user_auth0_sub)
    mock_get_memberships.assert_called_once_with(db=db_session, user_id=TEST_USER_ID, limit=1000)
    assert len(user_clubs) == 2
    # Check names to ensure correct clubs were extracted and sorted
    assert user_clubs[0].name == "Club A"
    assert user_clubs[1].name == "Club B"

# --- Tests for add_club_member --- (Illustrative Example)

@patch('backend.services.club_service.crud_membership.get_club_membership_by_user_and_club', new_callable=AsyncMock)
@patch('backend.services.club_service.crud_user.get_user_by_email', new_callable=AsyncMock)
@patch('backend.services.club_service.crud_membership.create_club_membership', new_callable=AsyncMock)
async def test_add_club_member_success(
    mock_create_membership: AsyncMock,
    mock_get_user_email: AsyncMock,
    mock_get_requestor_membership: AsyncMock,
    db_session: AsyncSession
):
    """ Test admin successfully adding a member. """
    # Arrange
    club_id = TEST_CLUB_ID
    requesting_user_obj = User(id=TEST_ADMIN_ID) # Assume this user object is passed in
    member_email_to_add = f"add_{uuid.uuid4().hex[:6]}@svc.test"
    role_to_add = ClubRole.MEMBER

    # Mock requestor is ADMIN
    mock_get_requestor_membership.return_value = ClubMembership(id=uuid.uuid4(), user_id=TEST_ADMIN_ID, club_id=club_id, role=ClubRole.ADMIN)

    # Mock finding the user to add by email
    mock_user_to_add = User(id=TEST_MEMBER_ID, email=member_email_to_add)
    mock_get_user_email.return_value = mock_user_to_add

    # Mock finding no existing membership for the user to add (needed for the check within add_club_member)
    # We need to configure the mock to return different values based on call args
    async def membership_side_effect(*args, **kwargs):
        if kwargs.get('user_id') == TEST_ADMIN_ID:
            return ClubMembership(id=uuid.uuid4(), user_id=TEST_ADMIN_ID, club_id=club_id, role=ClubRole.ADMIN)
        elif kwargs.get('user_id') == TEST_MEMBER_ID:
            return None # User to add is not already a member
        return None
    mock_get_requestor_membership.side_effect = membership_side_effect

    # Mock the successful creation of the new membership
    expected_membership = ClubMembership(id=TEST_MEMBERSHIP_ID, user_id=TEST_MEMBER_ID, club_id=club_id, role=role_to_add)
    mock_create_membership.return_value = expected_membership
    expected_create_data = {"user_id": TEST_MEMBER_ID, "club_id": club_id, "role": role_to_add}

    # Act
    result = await club_service.add_club_member(
        db=db_session, club_id=club_id, member_email=member_email_to_add, role=role_to_add, requesting_user=requesting_user_obj
    )

    # Assert
    # Check that get_club_membership was called twice (once for auth, once for existing check)
    assert mock_get_requestor_membership.call_count == 2
    mock_get_user_email.assert_called_once_with(db=db_session, email=member_email_to_add)
    mock_create_membership.assert_called_once_with(db=db_session, membership_data=expected_create_data)
    assert result == expected_membership


# --- Tests for update_member_role --- (Structure Example)

@patch('backend.services.club_service.crud_membership.get_club_membership_by_user_and_club', new_callable=AsyncMock)
@patch('backend.services.club_service.crud_membership.get_multi_club_memberships', new_callable=AsyncMock)
@patch('backend.services.club_service.crud_membership.update_club_membership', new_callable=AsyncMock)
async def test_update_member_role_success(
    mock_update_membership: AsyncMock,
    mock_get_multi_memberships: AsyncMock, # Mock for last admin check if needed
    mock_get_membership: AsyncMock,
    db_session: AsyncSession
):
    # Arrange
    club_id = TEST_CLUB_ID
    requesting_user_obj = User(id=TEST_ADMIN_ID)
    target_user_id = TEST_MEMBER_ID
    new_role = ClubRole.ADMIN

    # Mock requestor is ADMIN
    # Mock target membership exists with current role
    # Mock update success
    # Configure mocks...
    mock_admin_membership = ClubMembership(id=uuid.uuid4(), user_id=TEST_ADMIN_ID, club_id=club_id, role=ClubRole.ADMIN)
    mock_target_membership = ClubMembership(id=TEST_MEMBERSHIP_ID, user_id=target_user_id, club_id=club_id, role=ClubRole.MEMBER)

    async def get_membership_side_effect(*args, **kwargs):
         if kwargs.get('user_id') == TEST_ADMIN_ID: return mock_admin_membership
         if kwargs.get('user_id') == target_user_id: return mock_target_membership
         return None
    mock_get_membership.side_effect = get_membership_side_effect

    # Mock the update call return value
    mock_target_membership.role = new_role # Simulate update for return
    mock_update_membership.return_value = mock_target_membership

    # Act
    result = await club_service.update_member_role(
        db=db_session, club_id=club_id, member_user_id=target_user_id, new_role=new_role, requesting_user=requesting_user_obj
    )

    # Assert
    # Check get_membership called for requestor and target
    assert mock_get_membership.call_count == 2
    # Check update_membership called correctly
    mock_update_membership.assert_called_once()
    update_args, update_kwargs = mock_update_membership.call_args
    assert update_kwargs['db_obj'] == mock_target_membership # Passed the correct object
    assert isinstance(update_kwargs['obj_in'], ClubMembershipUpdate)
    assert update_kwargs['obj_in'].role == new_role # Passed the correct update schema
    assert result == mock_target_membership # Returned the updated object


# --- Tests for remove_club_member ---

# Keep existing mocks for balance check, add mocks for other CRUD ops
@patch('backend.services.club_service.crud_membership.get_club_membership_by_user_and_club', new_callable=AsyncMock)
@patch('backend.services.club_service.crud_membership.get_multi_club_memberships', new_callable=AsyncMock)
@patch('backend.crud.member_transaction.get_member_unit_balance', new_callable=AsyncMock) # Keep this one
@patch('backend.services.club_service.crud_membership.delete_club_membership', new_callable=AsyncMock)
async def test_remove_club_member_success(
    mock_delete_membership: AsyncMock,
    mock_get_balance: AsyncMock,
    mock_get_multi_memberships: AsyncMock, # Mock needed if last admin check happens
    mock_get_membership: AsyncMock,
    db_session: AsyncSession
):
    """ Test admin successfully removing a member with zero balance. """
    # Arrange
    club_id = TEST_CLUB_ID
    requesting_user_obj = User(id=TEST_ADMIN_ID)
    target_user_id = TEST_MEMBER_ID

    mock_get_balance.return_value = Decimal("0.0") # Mock zero balance

    # Mock finding admin and target memberships
    mock_admin_membership = ClubMembership(id=uuid.uuid4(), user_id=TEST_ADMIN_ID, club_id=club_id, role=ClubRole.ADMIN)
    mock_target_membership = ClubMembership(id=TEST_MEMBERSHIP_ID, user_id=target_user_id, club_id=club_id, role=ClubRole.MEMBER)
    async def get_membership_side_effect(*args, **kwargs):
         if kwargs.get('user_id') == TEST_ADMIN_ID: return mock_admin_membership
         if kwargs.get('user_id') == target_user_id: return mock_target_membership
         return None
    mock_get_membership.side_effect = get_membership_side_effect

    # Mock delete success (optional, depends if you need the return value)
    mock_delete_membership.return_value = mock_target_membership

    # Act
    result = await club_service.remove_club_member(
        db=db_session, club_id=club_id, member_user_id=target_user_id, requesting_user=requesting_user_obj
    )

    # Assert
    assert mock_get_membership.call_count == 2 # Called for auth and target
    mock_get_balance.assert_called_once_with(db=db_session, membership_id=TEST_MEMBERSHIP_ID)
    # mock_get_multi_memberships might be called if target role was admin (check logic)
    mock_delete_membership.assert_called_once_with(db=db_session, db_obj=mock_target_membership)
    assert result == mock_target_membership


@patch('backend.services.club_service.crud_membership.get_club_membership_by_user_and_club', new_callable=AsyncMock)
@patch('backend.crud.member_transaction.get_member_unit_balance', new_callable=AsyncMock) # Still need balance mock
async def test_remove_club_member_non_zero_balance(
    mock_get_balance: AsyncMock,
    mock_get_membership: AsyncMock,
    db_session: AsyncSession
):
    """ Test removing a member fails if they have a non-zero unit balance (mocked). """
    # Arrange
    club_id = TEST_CLUB_ID
    requesting_user_obj = User(id=TEST_ADMIN_ID)
    target_user_id = TEST_MEMBER_ID
    non_zero_balance = Decimal("100.50")
    mock_get_balance.return_value = non_zero_balance # Mock non-zero balance

    # Mock finding admin and target memberships
    mock_admin_membership = ClubMembership(id=uuid.uuid4(), user_id=TEST_ADMIN_ID, club_id=club_id, role=ClubRole.ADMIN)
    mock_target_membership = ClubMembership(id=TEST_MEMBERSHIP_ID, user_id=target_user_id, club_id=club_id, role=ClubRole.MEMBER)
    async def get_membership_side_effect(*args, **kwargs):
         if kwargs.get('user_id') == TEST_ADMIN_ID: return mock_admin_membership
         if kwargs.get('user_id') == target_user_id: return mock_target_membership
         return None
    mock_get_membership.side_effect = get_membership_side_effect

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await club_service.remove_club_member(
            db=db_session, club_id=club_id, member_user_id=target_user_id, requesting_user=requesting_user_obj
        )

    assert exc_info.value.status_code == 400
    assert f"unit balance is {non_zero_balance:.8f}" in exc_info.value.detail
    assert "must be 0" in exc_info.value.detail
    mock_get_membership.call_count == 2 # Auth and target checks
    mock_get_balance.assert_called_once_with(db=db_session, membership_id=TEST_MEMBERSHIP_ID)

# Add similar mocked tests for other scenarios:
# - test_remove_club_member_not_admin (mock auth check fails)
# - test_remove_club_member_self_removal_admin (check exception before balance check)
# - test_remove_club_member_last_admin (mock multi-membership check)
# - test_remove_club_member_target_not_found (mock target membership check returns None)