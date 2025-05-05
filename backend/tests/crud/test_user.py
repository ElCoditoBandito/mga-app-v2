# backend/tests/crud/test_user.py

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

# Import CRUD function and model
from backend.crud import user as user_crud
from backend.models import User
from backend.schemas import UserCreate, UserUpdate

# Mark all tests in this module to use the async environment
pytestmark = pytest.mark.asyncio


# --- Helper Function ---
async def create_test_user(
    db_session: AsyncSession,
    auth0_sub: str | None = None, # Make optional, default to None
    email: str | None = None,    # Make optional, default to None
    is_active: bool = True,
) -> User:
    """
    Helper function to create a user directly using CRUD.
    Generates unique email and auth0_sub if not provided.
    """
    # Generate unique values if not provided
    if email is None:
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    if auth0_sub is None:
        auth0_sub = f"auth0|test_{uuid.uuid4().hex[:12]}" # Always generate unique if None

    user_data = {"auth0_sub": auth0_sub, "email": email, "is_active": is_active}
    user = await user_crud.create_user(db=db_session, user_data=user_data) # [cite: backend_files/crud/user.py]
    assert user.email == email
    assert user.auth0_sub == auth0_sub
    return user

# --- CRUD Tests ---

async def test_create_user(db_session: AsyncSession):
    """Test creating a user."""
    auth0_sub = f"auth0|{uuid.uuid4()}"
    email = f"test_create_{uuid.uuid4().hex[:6]}@example.com"
    user_data = {"auth0_sub": auth0_sub, "email": email, "is_active": True}
    user = await user_crud.create_user(db=db_session, user_data=user_data)
    assert user.email == email
    assert user.auth0_sub == auth0_sub
    assert user.is_active is True
    assert user.id is not None


async def test_get_user(db_session: AsyncSession):
    """Test getting a user by ID."""
    user = await create_test_user(db_session) # Use helper
    fetched_user = await user_crud.get_user(db=db_session, user_id=user.id)
    assert fetched_user
    assert fetched_user.id == user.id
    assert fetched_user.email == user.email


async def test_get_user_not_found(db_session: AsyncSession):
    """Test getting a non-existent user by ID."""
    non_existent_id = uuid.uuid4()
    fetched_user = await user_crud.get_user(db=db_session, user_id=non_existent_id)
    assert fetched_user is None


async def test_get_user_by_email(db_session: AsyncSession):
    """Test getting a user by email."""
    user = await create_test_user(db_session) # Use helper
    fetched_user = await user_crud.get_user_by_email(db=db_session, email=user.email)
    assert fetched_user
    assert fetched_user.id == user.id
    assert fetched_user.email == user.email


async def test_get_user_by_email_not_found(db_session: AsyncSession):
    """Test getting a user by non-existent email."""
    email = "nonexistent@example.com"
    fetched_user = await user_crud.get_user_by_email(db=db_session, email=email)
    assert fetched_user is None


async def test_get_user_by_auth0_sub(db_session: AsyncSession):
    """Test getting a user by auth0_sub."""
    user = await create_test_user(db_session) # Use helper
    fetched_user = await user_crud.get_user_by_auth0_sub(db=db_session, auth0_sub=user.auth0_sub)
    assert fetched_user
    assert fetched_user.id == user.id
    assert fetched_user.auth0_sub == user.auth0_sub


async def test_get_user_by_auth0_sub_not_found(db_session: AsyncSession):
    """Test getting a user by non-existent auth0_sub."""
    auth0_sub = "auth0|nonexistent"
    fetched_user = await user_crud.get_user_by_auth0_sub(db=db_session, auth0_sub=auth0_sub)
    assert fetched_user is None


async def test_get_users(db_session: AsyncSession):
    """Test getting multiple users."""
    user1 = await create_test_user(db_session)
    user2 = await create_test_user(db_session)
    users = await user_crud.get_users(db=db_session, skip=0, limit=10)
    assert len(users) >= 2
    user_ids = {u.id for u in users}
    assert user1.id in user_ids
    assert user2.id in user_ids


async def test_update_user(db_session: AsyncSession):
    """Test updating a user (only is_active can be updated)."""
    user = await create_test_user(db_session, is_active=True)
    assert user.is_active is True

    # Update to inactive
    update_schema_inactive = UserUpdate(is_active=False)
    updated_user = await user_crud.update_user(db=db_session, db_user=user, user_in=update_schema_inactive)
    assert updated_user.is_active is False

    # Verify change persisted
    fetched_user = await user_crud.get_user(db=db_session, user_id=user.id)
    assert fetched_user.is_active is False

    # Try updating email and is_active back to True
    original_email = user.email # Store original email for context if needed
    new_email = "ignored@example.com" # Define the new email being tested
    update_schema_active_email = UserUpdate(email=new_email, is_active=True)

    assert fetched_user is not None, "Fetched user should exist for second update"
    updated_user_ignore = await user_crud.update_user(db=db_session, db_user=fetched_user, user_in=update_schema_active_email) #
   
    assert updated_user_ignore.email == new_email # Assert email WAS updated to the value provided
    assert updated_user_ignore.is_active is True # is_active should change


async def test_delete_user(db_session: AsyncSession):
    """Test deleting a user."""
    user = await create_test_user(db_session)
    deleted_user = await user_crud.delete_user(db=db_session, db_user=user)
    assert deleted_user.id == user.id

    # Verify deletion
    fetched_user = await user_crud.get_user(db=db_session, user_id=user.id)
    assert fetched_user is None

