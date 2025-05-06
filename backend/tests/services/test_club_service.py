# backend/tests/services/test_club_service.py

import pytest
import uuid
from decimal import Decimal
from unittest.mock import patch, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

# Service functions to test
from backend.services import club_service
# CRUD functions - now used directly instead of mocked
from backend.crud import club as crud_club
from backend.crud import user as crud_user
from backend.crud import fund as crud_fund
from backend.crud import club_membership as crud_membership
from backend.crud import member_transaction as crud_member_transaction
# Models and Schemas
from backend.models import User, Club, Fund, ClubMembership
from backend.models.enums import ClubRole
from backend.schemas import ClubCreate, ClubMembershipUpdate

# Import Auth0 mocking fixtures
from backend.tests.auth_fixtures import mock_auth0_token_verification, mock_get_current_active_user, test_user

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio

# --- Tests for create_club ---

async def test_create_club_success(db_session: AsyncSession, test_user: User):
    """ Test successful club creation including default fund and admin membership using actual CRUD functions. """
    # Arrange
    club_name = f"Test Club {uuid.uuid4().hex[:6]}"
    club_in = ClubCreate(name=club_name, description="Testing creation with real CRUD")

    # Act
    created_club = await club_service.create_club(
        db=db_session, 
        club_in=club_in, 
        auth0_sub=test_user.auth0_sub
    )

    # Assert
    assert created_club is not None
    assert created_club.name == club_name
    assert created_club.description == club_in.description
    assert created_club.creator_id == test_user.id

    # Verify the default fund was created
    funds = await crud_fund.get_multi_funds(db=db_session, club_id=created_club.id)
    assert len(funds) == 1
    assert funds[0].name == "General Fund"
    
    # Verify admin membership was created
    membership = await crud_membership.get_club_membership_by_user_and_club(
        db=db_session, 
        user_id=test_user.id, 
        club_id=created_club.id
    )
    assert membership is not None
    assert membership.role == ClubRole.ADMIN


async def test_create_club_user_not_found(db_session: AsyncSession):
    """ Test club creation fails if the requesting user doesn't exist. """
    # Arrange
    non_existent_auth0_sub = f"auth0|no_such_user_{uuid.uuid4().hex}"
    club_in = ClubCreate(name="Wont Be Created", description="")

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await club_service.create_club(db=db_session, club_in=club_in, auth0_sub=non_existent_auth0_sub)

    assert exc_info.value.status_code == 404
    assert f"User with auth0_sub '{non_existent_auth0_sub}' not found" in exc_info.value.detail


# --- Tests for get_club_details ---

async def test_get_club_details_found(db_session: AsyncSession, test_user: User):
    """ Test retrieving details for an existing club using actual CRUD functions. """
    # Arrange - Create a club first
    club_name = f"Club Details {uuid.uuid4().hex[:6]}"
    club_data = {
        "name": club_name,
        "description": "Test club for details",
        "creator_id": test_user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()

    # Act
    fetched_club = await club_service.get_club_details(db=db_session, club_id=club.id)

    # Assert
    assert fetched_club is not None
    assert fetched_club.id == club.id
    assert fetched_club.name == club_name


async def test_get_club_details_not_found(db_session: AsyncSession):
    """ Test retrieving details for a non-existent club. """
    # Arrange
    non_existent_club_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await club_service.get_club_details(db=db_session, club_id=non_existent_club_id)

    assert exc_info.value.status_code == 404
    assert f"Club with id {non_existent_club_id} not found" in exc_info.value.detail


# --- Tests for list_user_clubs ---

async def test_list_user_clubs_multiple(db_session: AsyncSession, test_user: User):
    """ Test listing multiple clubs for a single user using actual CRUD functions. """
    # Arrange - Create two clubs and add the user to both
    club1_data = {
        "name": f"Club A {uuid.uuid4().hex[:6]}",
        "description": "First test club",
        "creator_id": test_user.id
    }
    club2_data = {
        "name": f"Club B {uuid.uuid4().hex[:6]}",
        "description": "Second test club",
        "creator_id": test_user.id
    }
    
    club1 = await crud_club.create_club(db=db_session, club_data=club1_data)
    club2 = await crud_club.create_club(db=db_session, club_data=club2_data)
    await db_session.flush()
    
    # Create memberships
    membership1_data = {
        "user_id": test_user.id,
        "club_id": club1.id,
        "role": ClubRole.MEMBER
    }
    membership2_data = {
        "user_id": test_user.id,
        "club_id": club2.id,
        "role": ClubRole.ADMIN
    }
    
    await crud_membership.create_club_membership(db=db_session, membership_data=membership1_data)
    await crud_membership.create_club_membership(db=db_session, membership_data=membership2_data)
    await db_session.flush()

    # Act
    user_clubs = await club_service.list_user_clubs(db=db_session, auth0_sub=test_user.auth0_sub)

    # Assert
    assert len(user_clubs) == 2
    # Check that both clubs are in the result (order might vary)
    club_names = [club.name for club in user_clubs]
    assert club1.name in club_names
    assert club2.name in club_names


# --- Tests for add_club_member ---

async def test_add_club_member_success(db_session: AsyncSession):
    """ Test admin successfully adding a member using actual CRUD functions. """
    # Arrange - Create admin user, member user, and a club
    admin_data = {
        "email": f"admin_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|admin_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    member_data = {
        "email": f"member_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|member_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    
    admin_user = await crud_user.create_user(db=db_session, user_data=admin_data)
    member_user = await crud_user.create_user(db=db_session, user_data=member_data)
    await db_session.flush()
    
    club_data = {
        "name": f"Club Add Member {uuid.uuid4().hex[:6]}",
        "description": "Test club for adding members",
        "creator_id": admin_user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    # Create admin membership
    admin_membership_data = {
        "user_id": admin_user.id,
        "club_id": club.id,
        "role": ClubRole.ADMIN
    }
    await crud_membership.create_club_membership(db=db_session, membership_data=admin_membership_data)
    await db_session.flush()

    # Act
    result = await club_service.add_club_member(
        db=db_session, 
        club_id=club.id, 
        member_email=member_user.email, 
        role=ClubRole.MEMBER, 
        requesting_user=admin_user
    )

    # Assert
    assert result is not None
    assert result.user_id == member_user.id
    assert result.club_id == club.id
    assert result.role == ClubRole.MEMBER
    
    # Verify membership exists in database
    db_membership = await crud_membership.get_club_membership_by_user_and_club(
        db=db_session,
        user_id=member_user.id,
        club_id=club.id
    )
    assert db_membership is not None
    assert db_membership.role == ClubRole.MEMBER


# --- Tests for update_member_role ---

async def test_update_member_role_success(db_session: AsyncSession):
    """ Test admin successfully updating a member's role using actual CRUD functions. """
    # Arrange - Create admin user, member user, and a club with memberships
    admin_data = {
        "email": f"admin_update_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|admin_update_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    member_data = {
        "email": f"member_update_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|member_update_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    
    admin_user = await crud_user.create_user(db=db_session, user_data=admin_data)
    member_user = await crud_user.create_user(db=db_session, user_data=member_data)
    await db_session.flush()
    
    club_data = {
        "name": f"Club Update Role {uuid.uuid4().hex[:6]}",
        "description": "Test club for updating roles",
        "creator_id": admin_user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    # Create memberships
    admin_membership_data = {
        "user_id": admin_user.id,
        "club_id": club.id,
        "role": ClubRole.ADMIN
    }
    member_membership_data = {
        "user_id": member_user.id,
        "club_id": club.id,
        "role": ClubRole.MEMBER
    }
    
    await crud_membership.create_club_membership(db=db_session, membership_data=admin_membership_data)
    await crud_membership.create_club_membership(db=db_session, membership_data=member_membership_data)
    await db_session.flush()

    # Act
    result = await club_service.update_member_role(
        db=db_session,
        club_id=club.id,
        member_user_id=member_user.id,
        new_role=ClubRole.ADMIN,
        requesting_user=admin_user
    )

    # Assert
    assert result is not None
    assert result.user_id == member_user.id
    assert result.club_id == club.id
    assert result.role == ClubRole.ADMIN
    
    # Verify role was updated in database
    db_membership = await crud_membership.get_club_membership_by_user_and_club(
        db=db_session,
        user_id=member_user.id,
        club_id=club.id
    )
    assert db_membership is not None
    assert db_membership.role == ClubRole.ADMIN


# --- Tests for remove_club_member ---

async def test_remove_club_member_success(db_session: AsyncSession):
    """ Test admin successfully removing a member with zero balance using actual CRUD functions. """
    # Arrange - Create admin user, member user, and a club with memberships
    admin_data = {
        "email": f"admin_remove_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|admin_remove_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    member_data = {
        "email": f"member_remove_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|member_remove_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    
    admin_user = await crud_user.create_user(db=db_session, user_data=admin_data)
    member_user = await crud_user.create_user(db=db_session, user_data=member_data)
    await db_session.flush()
    
    club_data = {
        "name": f"Club Remove Member {uuid.uuid4().hex[:6]}",
        "description": "Test club for removing members",
        "creator_id": admin_user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    # Create memberships
    admin_membership_data = {
        "user_id": admin_user.id,
        "club_id": club.id,
        "role": ClubRole.ADMIN
    }
    member_membership_data = {
        "user_id": member_user.id,
        "club_id": club.id,
        "role": ClubRole.MEMBER
    }
    
    await crud_membership.create_club_membership(db=db_session, membership_data=admin_membership_data)
    member_membership = await crud_membership.create_club_membership(db=db_session, membership_data=member_membership_data)
    await db_session.flush()
    
    # Act
    result = await club_service.remove_club_member(
        db=db_session,
        club_id=club.id,
        member_user_id=member_user.id,
        requesting_user=admin_user
    )
    
    # Assert
    assert result is not None
    assert result.user_id == member_user.id
    assert result.club_id == club.id
    
    # Verify membership was removed from database
    db_membership = await crud_membership.get_club_membership_by_user_and_club(
        db=db_session,
        user_id=member_user.id,
        club_id=club.id
    )
    assert db_membership is None


async def test_remove_club_member_non_zero_balance(db_session: AsyncSession):
    """ Test removing a member fails if they have a non-zero unit balance. """
    # Arrange - Create admin user, member user, and a club with memberships
    admin_data = {
        "email": f"admin_balance_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|admin_balance_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    member_data = {
        "email": f"member_balance_{uuid.uuid4().hex[:6]}@example.com",
        "auth0_sub": f"auth0|member_balance_{uuid.uuid4().hex[:6]}",
        "is_active": True
    }
    
    admin_user = await crud_user.create_user(db=db_session, user_data=admin_data)
    member_user = await crud_user.create_user(db=db_session, user_data=member_data)
    await db_session.flush()
    
    club_data = {
        "name": f"Club Balance Check {uuid.uuid4().hex[:6]}",
        "description": "Test club for balance check",
        "creator_id": admin_user.id
    }
    club = await crud_club.create_club(db=db_session, club_data=club_data)
    await db_session.flush()
    
    # Create memberships
    admin_membership_data = {
        "user_id": admin_user.id,
        "club_id": club.id,
        "role": ClubRole.ADMIN
    }
    member_membership_data = {
        "user_id": member_user.id,
        "club_id": club.id,
        "role": ClubRole.MEMBER
    }
    
    await crud_membership.create_club_membership(db=db_session, membership_data=admin_membership_data)
    member_membership = await crud_membership.create_club_membership(db=db_session, membership_data=member_membership_data)
    await db_session.flush()
    
    # Create a transaction to give the member a non-zero balance
    from backend.models.enums import MemberTransactionType
    from datetime import datetime, timezone
    
    # Create a deposit transaction
    deposit_data = {
        "membership_id": member_membership.id,
        "transaction_type": MemberTransactionType.DEPOSIT,
        "amount": Decimal("1000.00"),
        "transaction_date": datetime.now(timezone.utc),
        "unit_value_used": Decimal("10.00"),
        "units_transacted": Decimal("100.00"),
        "notes": "Test deposit for non-zero balance"
    }
    
    await crud_member_transaction.create_member_transaction(
        db=db_session,
        member_tx_data=deposit_data
    )
    await db_session.flush()
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await club_service.remove_club_member(
            db=db_session,
            club_id=club.id,
            member_user_id=member_user.id,
            requesting_user=admin_user
        )
    
    assert exc_info.value.status_code == 400
    assert "unit balance is" in exc_info.value.detail
    assert "must be 0" in exc_info.value.detail
    
    # Verify membership still exists in database
    db_membership = await crud_membership.get_club_membership_by_user_and_club(
        db=db_session,
        user_id=member_user.id,
        club_id=club.id
    )
    assert db_membership is not None