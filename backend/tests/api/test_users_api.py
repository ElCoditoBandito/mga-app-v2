# backend/tests/api/test_users_api.py

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient # Use httpx.AsyncClient for async requests with TestClient
from fastapi import status

# Import the FastAPI app instance
from backend.main import app

# Import schemas and models
from backend.schemas import UserRead
from backend.models import User as UserModel

# Import fixtures
from backend.tests.auth_fixtures import authenticated_user # Fixture to mock auth and provide user

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio


# --- Test Fixture for API Client ---
# Provides an instance of TestClient for making requests to the app
@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an asynchronous test client for the FastAPI application.
    """
    # Use httpx.AsyncClient with the FastAPI app instance
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client

# --- API Tests ---

async def test_read_users_me_success(
    client: AsyncClient,
    authenticated_user: UserModel # Use the fixture that mocks auth and provides the user
):
    """
    Test GET /users/me endpoint for a successfully authenticated user.
    """
    # Arrange:
    # The 'authenticated_user' fixture handles mocking the authentication dependency
    # and ensures the user exists in the test database (via the 'test_user' fixture it depends on).
    # We expect the API to return this user's details.
    expected_user = authenticated_user

    # Act:
    # Make a GET request to the /api/v1/users/me endpoint.
    # The client automatically handles the base URL.
    # No explicit headers needed here because the dependency is mocked by authenticated_user fixture.
    response = await client.get("/api/v1/users/me")

    # Assert:
    # Check for successful status code
    assert response.status_code == status.HTTP_200_OK

    # Parse the response JSON
    response_data = response.json()

    # Validate the response against the UserRead schema
    # This ensures the response structure and types are correct.
    # Pydantic will raise an error if validation fails.
    user_response = UserRead(**response_data)

    # Check if the returned user data matches the expected user from the fixture
    assert user_response.id == expected_user.id
    assert user_response.email == expected_user.email
    assert user_response.auth0_sub == expected_user.auth0_sub
    assert user_response.is_active == expected_user.is_active


async def test_read_users_me_unauthenticated(
    client: AsyncClient
):
    """
    Test GET /users/me endpoint without authentication.
    Expects a 401 Unauthorized error because the dependency is NOT mocked here.
    """
    # Arrange: No authentication headers are sent.

    # Act:
    response = await client.get("/api/v1/users/me")

    # Assert:
    # The HTTPBearer dependency should automatically return 401
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # Optionally check the detail message if it's consistent
    # response_data = response.json()
    # assert response_data["detail"] == "Not authenticated" # Or whatever HTTPBearer returns

