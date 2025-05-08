# backend/tests/auth_fixtures.py

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import JWTPayload
from backend.models import User as UserModel
from backend.crud import user as crud_user

log = logging.getLogger(__name__)

# --- Auth0 Mock Fixtures ---

@pytest.fixture
def mock_auth0_token_verification():
    """
    Fixture to mock Auth0 token verification.
    Returns a function that can be used to patch verify_token.
    """
    
    async def mock_verify_token(token: str) -> JWTPayload:
        """Mock implementation that returns a predefined payload."""
        # Create a fake payload that matches the JWTPayload model
        # Include the custom org_id claim in the raw payload
        payload = {
            "sub": "auth0|test_user",
            "iss": "https://test-domain.auth0.com/",
            "aud": ["test-audience"],
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "email": "test@example.com",
            "https://api.mga-app.com/org_id": "test_org_id"  # Add the organization ID claim
        }
        return JWTPayload(**payload)
    
    return mock_verify_token

@pytest.fixture
def mock_get_current_active_user(mock_auth0_token_verification):
    """
    Fixture to mock the get_current_active_user dependency.
    """
    
    # Create the patch
    patcher = patch('backend.api.dependencies.verify_token', mock_auth0_token_verification)
    
    # Start the patch
    patcher.start()
    
    # Make sure to stop the patch when the test is done
    yield
    
    # Stop the patch
    patcher.stop()

# --- Test User Fixture ---

@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> UserModel:
    """
    Creates a reusable, active test user in the database for function scope.
    Uses the actual user CRUD function.
    """
    unique_id = uuid.uuid4()
    user_data = {
        "email": f"testuser_{unique_id}@example.com",
        "auth0_sub": f"auth0|test_{unique_id}",
        "is_active": True
    }
    
    log.debug(f"Creating test user with email: {user_data['email']}")
    try:
        # Use the actual CRUD function with a dictionary
        user = await crud_user.create_user(db=db_session, user_data=user_data)
        # The db_session fixture handles rollback, so we don't commit here
        await db_session.flush()
        await db_session.refresh(user)
        log.debug(f"Created test user with ID: {user.id}")
        return user
    except Exception as e:
        log.exception(f"Failed to create test user: {e}")
        pytest.fail(f"Failed to create test user: {e}")

@pytest_asyncio.fixture(scope="function")
async def authenticated_user(db_session: AsyncSession, test_user: UserModel):
    """
    Fixture that provides a test user and mocks the authentication system
    to return this user as the current authenticated user.
    """
    
    # Create a mock for get_current_active_user that returns our test user
    mock_get_current_user = AsyncMock(return_value=test_user)
    
    # Apply the patch
    with patch('backend.api.dependencies.get_current_active_user', mock_get_current_user):
        yield test_user