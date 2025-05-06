# backend/tests/services/test_user_service.py

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from unittest.mock import patch, AsyncMock

# Service function to test
from backend.services import user_service
# CRUD functions - now used directly instead of mocked
from backend.crud import user as crud_user
# Models and Schemas
from backend.models import User

# Import our Auth0 mocking fixtures
from backend.tests.auth_fixtures import mock_auth0_token_verification, mock_get_current_active_user, test_user

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio


async def test_get_or_create_user_existing(db_session: AsyncSession):
    """
    Test get_or_create_user_by_auth0 when the user already exists.
    Uses actual CRUD functions with the database.
    """
    # Arrange: Create an existing user directly using CRUD
    auth0_sub = f"auth0|exists_{uuid.uuid4()}"
    email = f"existing_{uuid.uuid4()}@example.com"
    
    # Create user directly with CRUD
    user_data = {
        "auth0_sub": auth0_sub,
        "email": email,
        "is_active": True
    }
    existing_user = await crud_user.create_user(db=db_session, user_data=user_data)
    await db_session.flush()
    
    # Act: Call the service function with the same details
    retrieved_or_created_user = await user_service.get_or_create_user_by_auth0(
        db=db_session,
        auth0_sub=auth0_sub,
        email=email
    )

    # Assert: Check if the returned user is the existing one
    assert retrieved_or_created_user is not None
    assert retrieved_or_created_user.id == existing_user.id
    assert retrieved_or_created_user.auth0_sub == auth0_sub
    assert retrieved_or_created_user.email == email


async def test_get_or_create_user_new(db_session: AsyncSession):
    """
    Test get_or_create_user_by_auth0 when the user does not exist.
    Uses actual CRUD functions with the database.
    """
    # Arrange: Define details for a new user
    auth0_sub = f"auth0|new_{uuid.uuid4()}"
    email = f"new_{uuid.uuid4()}@example.com"

    # Act: Call the service function
    retrieved_or_created_user = await user_service.get_or_create_user_by_auth0(
        db=db_session,
        auth0_sub=auth0_sub,
        email=email
    )

    # Assert: Check if a new user was created with correct details
    assert retrieved_or_created_user is not None
    assert isinstance(retrieved_or_created_user, User)
    assert retrieved_or_created_user.auth0_sub == auth0_sub
    assert retrieved_or_created_user.email == email
    assert retrieved_or_created_user.is_active is True  # Default
    assert retrieved_or_created_user.id is not None
    
    # Verify the user exists in the database
    db_user = await crud_user.get_user_by_auth0_sub(db=db_session, auth0_sub=auth0_sub)
    assert db_user is not None
    assert db_user.id == retrieved_or_created_user.id


async def test_get_or_create_user_integrity_error(db_session: AsyncSession):
    """
    Test get_or_create_user_by_auth0 when creation fails due to existing email
    but different auth0_sub (simulating data inconsistency).
    Uses actual CRUD functions with the database.
    """
    # Arrange: Create a user with a specific email
    email = f"conflict_{uuid.uuid4()}@example.com"
    initial_auth0_sub = f"auth0|initial_{uuid.uuid4()}"
    
    # Create initial user
    user_data = {
        "auth0_sub": initial_auth0_sub,
        "email": email,
        "is_active": True
    }
    await crud_user.create_user(db=db_session, user_data=user_data)
    await db_session.flush()

    # Define details for the conflicting creation attempt
    conflicting_auth0_sub = f"auth0|conflict_{uuid.uuid4()}"

    # Act & Assert: Call the service function and expect an HTTPException 409
    with pytest.raises(HTTPException) as exc_info:
        await user_service.get_or_create_user_by_auth0(
            db=db_session,
            auth0_sub=conflicting_auth0_sub,  # Different auth0_sub
            email=email  # Same email
        )

    # Check the exception details
    assert exc_info.value.status_code == 409  # Conflict
    assert f"Email '{email}' might already be associated" in exc_info.value.detail


# Test with the authenticated_user fixture to verify Auth0 mocking
# Import the specific fixture
from backend.tests.auth_fixtures import authenticated_user

async def test_authenticated_user_fixture(
    db_session: AsyncSession, # Keep db_session if needed by other parts
    authenticated_user: User # Use the fixture directly
):
    """
    Test that the authenticated_user fixture correctly provides the user
    and mocks the dependency.
    """
    # Arrange: The fixture handles setup and mocking.
    # 'authenticated_user' is the resolved User object.

    # Act: (Optional) You could call an endpoint/service that uses
    # the get_current_active_user dependency here if you wanted to test integration.
    # For this test, simply verifying the fixture worked is enough.

    # Assert: Verify the fixture provided the correct user object
    assert authenticated_user is not None
    assert isinstance(authenticated_user, User)
    assert authenticated_user.auth0_sub is not None
    assert authenticated_user.email is not None

    # You could add further checks, e.g., fetch the user from DB to ensure it exists
    db_user = await crud_user.get_user(db=db_session, user_id=authenticated_user.id)
    assert db_user is not None
    assert db_user.id == authenticated_user.id