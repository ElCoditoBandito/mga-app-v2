# backend/tests/services/test_user_service.py

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException # To check for expected exceptions
from unittest.mock import patch, AsyncMock # Import necessary mocking tools

# Service function to test
from backend.services import user_service
# CRUD function for verification and setup - Mocked usually
# from backend.crud import user as crud_user
# Models and Schemas
from backend.models import User

# Use helpers from CRUD tests for setup if needed - Not typically needed if mocking CRUD
# from backend.tests.crud.test_user import create_test_user

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio


# Use patch to mock the CRUD functions within the user_service module's scope
@patch('backend.services.user_service.crud_user.get_user_by_auth0_sub', new_callable=AsyncMock)
@patch('backend.services.user_service.crud_user.create_user', new_callable=AsyncMock)
async def test_get_or_create_user_existing(
    mock_create_user: AsyncMock,
    mock_get_user: AsyncMock,
    db_session: AsyncSession # db_session fixture is still useful for passing to the service
):
    """
    Test get_or_create_user_by_auth0 when the user already exists.
    Mocks CRUD functions.
    """
    # Arrange
    auth0_sub = f"auth0|exists_{uuid.uuid4()}"
    email = f"existing_{uuid.uuid4()}@example.com"
    # Define the mock return value for get_user_by_auth0_sub
    existing_user_obj = User(id=uuid.uuid4(), auth0_sub=auth0_sub, email=email, is_active=True)
    mock_get_user.return_value = existing_user_obj

    # Act
    retrieved_or_created_user = await user_service.get_or_create_user_by_auth0(
        db=db_session,
        auth0_sub=auth0_sub,
        email=email
    )

    # Assert
    # Verify get_user was called correctly
    mock_get_user.assert_called_once_with(db=db_session, auth0_sub=auth0_sub)
    # Verify create_user was NOT called
    mock_create_user.assert_not_called()
    # Verify the returned user is the one returned by the mock
    assert retrieved_or_created_user is not None
    assert retrieved_or_created_user.id == existing_user_obj.id
    assert retrieved_or_created_user.auth0_sub == auth0_sub
    assert retrieved_or_created_user.email == email

@patch('backend.services.user_service.crud_user.get_user_by_auth0_sub', new_callable=AsyncMock)
@patch('backend.services.user_service.crud_user.create_user', new_callable=AsyncMock)
async def test_get_or_create_user_new(
    mock_create_user: AsyncMock,
    mock_get_user: AsyncMock,
    db_session: AsyncSession
):
    """
    Test get_or_create_user_by_auth0 when the user does not exist.
    Mocks CRUD functions.
    """
    # Arrange
    auth0_sub = f"auth0|new_{uuid.uuid4()}"
    email = f"new_{uuid.uuid4()}@example.com"
    # Simulate get_user finding nothing
    mock_get_user.return_value = None
    # Define the user object that create_user should return
    new_user_obj = User(id=uuid.uuid4(), auth0_sub=auth0_sub, email=email, is_active=True)
    mock_create_user.return_value = new_user_obj
    # Expected data passed to create_user
    expected_create_data = {"auth0_sub": auth0_sub, "email": email}

    # Act
    retrieved_or_created_user = await user_service.get_or_create_user_by_auth0(
        db=db_session,
        auth0_sub=auth0_sub,
        email=email
    )

    # Assert
    # Verify get_user was called
    mock_get_user.assert_called_once_with(db=db_session, auth0_sub=auth0_sub)
    # Verify create_user was called with the correct data
    mock_create_user.assert_called_once_with(db=db_session, user_data=expected_create_data)
    # Verify the returned user is the one returned by the mock create_user
    assert retrieved_or_created_user is not None
    assert retrieved_or_created_user.id == new_user_obj.id
    assert retrieved_or_created_user.auth0_sub == auth0_sub
    assert retrieved_or_created_user.email == email

@patch('backend.services.user_service.crud_user.get_user_by_auth0_sub', new_callable=AsyncMock)
@patch('backend.services.user_service.crud_user.create_user', new_callable=AsyncMock)
async def test_get_or_create_user_integrity_error_on_create(
    mock_create_user: AsyncMock,
    mock_get_user: AsyncMock,
    db_session: AsyncSession
):
    """
    Test get_or_create_user_by_auth0 handles IntegrityError during creation.
    Mocks CRUD functions.
    """
    # Arrange
    auth0_sub = f"auth0|conflict_{uuid.uuid4()}"
    email = f"conflict_{uuid.uuid4()}@example.com"
    # Simulate get_user finding nothing
    mock_get_user.return_value = None
    # Simulate create_user raising IntegrityError (from sqlalchemy.exc import IntegrityError)
    # Need to import IntegrityError for this test
    from sqlalchemy.exc import IntegrityError
    mock_create_user.side_effect = IntegrityError("Mock Integrity Error", params={}, orig=Exception())

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await user_service.get_or_create_user_by_auth0(
            db=db_session,
            auth0_sub=auth0_sub,
            email=email
        )

    # Verify exception details
    assert exc_info.value.status_code == 409 # Conflict
    assert f"Email '{email}' might already be associated" in exc_info.value.detail
    # Verify mocks were called as expected before the error
    mock_get_user.assert_called_once_with(db=db_session, auth0_sub=auth0_sub)
    mock_create_user.assert_called_once()

# --- Previous CRUD-based tests (can be removed or kept for reference) ---
# The tests below hit the database via CRUD helpers. They are more like integration tests
# for the CRUD layer than unit tests for the service layer logic.
# It's generally better to mock the CRUD layer for service tests as shown above.

# async def test_get_or_create_user_existing(db_session: AsyncSession):
#     """
#     Test get_or_create_user_by_auth0 when the user already exists.
#     (Original version hitting DB via CRUD helper)
#     """
#     # 1. Arrange: Create an existing user directly using CRUD helper
#     auth0_sub = f"auth0|exists_{uuid.uuid4()}"
#     email = f"existing_{uuid.uuid4()}@example.com"
#     existing_user = await create_test_user(db_session, auth0_sub=auth0_sub, email=email)
#     assert existing_user is not None

#     # 2. Act: Call the service function with the same details
#     retrieved_or_created_user = await user_service.get_or_create_user_by_auth0(
#         db=db_session,
#         auth0_sub=auth0_sub,
#         email=email
#     ) #

#     # 3. Assert: Check if the returned user is the existing one
#     assert retrieved_or_created_user is not None
#     assert retrieved_or_created_user.id == existing_user.id
#     assert retrieved_or_created_user.auth0_sub == auth0_sub
#     assert retrieved_or_created_user.email == email


# async def test_get_or_create_user_new(db_session: AsyncSession):
#     """
#     Test get_or_create_user_by_auth0 when the user does not exist.
#      (Original version hitting DB via CRUD helper)
#     """
#     # 1. Arrange: Define details for a new user
#     auth0_sub = f"auth0|new_{uuid.uuid4()}"
#     email = f"new_{uuid.uuid4()}@example.com"

#     # 2. Act: Call the service function
#     retrieved_or_created_user = await user_service.get_or_create_user_by_auth0(
#         db=db_session,
#         auth0_sub=auth0_sub,
#         email=email
#     ) #

#     # 3. Assert: Check if a new user was created with correct details
#     assert retrieved_or_created_user is not None
#     assert isinstance(retrieved_or_created_user, User)
#     assert retrieved_or_created_user.auth0_sub == auth0_sub
#     assert retrieved_or_created_user.email == email
#     assert retrieved_or_created_user.is_active is True # Default
#     assert retrieved_or_created_user.id is not None


# async def test_get_or_create_user_integrity_error(db_session: AsyncSession):
#     """
#     Test get_or_create_user_by_auth0 when creation fails due to existing email
#     but different auth0_sub (simulating data inconsistency).
#      (Original version hitting DB via CRUD helper)
#     """
#     # 1. Arrange: Create a user with a specific email
#     email = f"conflict_{uuid.uuid4()}@example.com"
#     initial_auth0_sub = f"auth0|initial_{uuid.uuid4()}"
#     await create_test_user(db_session, auth0_sub=initial_auth0_sub, email=email)

#     # Define details for the conflicting creation attempt
#     conflicting_auth0_sub = f"auth0|conflict_{uuid.uuid4()}"

#     # 2. Act & Assert: Call the service function and expect an HTTPException 409
#     with pytest.raises(HTTPException) as exc_info:
#         await user_service.get_or_create_user_by_auth0(
#             db=db_session,
#             auth0_sub=conflicting_auth0_sub, # Different auth0_sub
#             email=email # Same email
#         ) #

#     # Check the exception details
#     assert exc_info.value.status_code == 409 # Conflict
#     assert f"Email '{email}' might already be associated" in exc_info.value.detail