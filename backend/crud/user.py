# backend/crud/user.py

import uuid
from typing import List, Optional, Dict, Any # Added Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Assuming your models are structured like this
from backend.models import User as UserModel
# Assuming your schemas are structured like this
# No longer need UserCreate here
from backend.schemas import user as UserSchema


# --- Create ---
async def create_user(db: AsyncSession, *, user_data: Dict[str, Any]) -> UserModel:
    """
    Creates a new user in the database from a dictionary.

    Args:
        db: The AsyncSession instance.
        user_data: Dictionary containing user data ('email', 'auth0_sub', optional 'is_active').
                   Must be passed as a keyword argument.

    Returns:
        The newly created User model instance.
    """
    # Filter data to match model attributes
    model_data = {k: v for k, v in user_data.items() if hasattr(UserModel, k)}

    # Optional check for required fields
    # required_fields = ['email', 'auth0_sub']
    # if not all(k in model_data for k in required_fields):
    #     raise ValueError("Missing required fields for User model")

    # Set default for is_active if not provided
    model_data.setdefault('is_active', True)

    db_user = UserModel(**model_data)
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user

# --- Read ---
async def get_user(db: AsyncSession, *, user_id: uuid.UUID) -> Optional[UserModel]:
    """
    Retrieves a single user by their unique ID.

    Args:
        db: The AsyncSession instance.
        user_id: The UUID of the user to retrieve.
                 Must be passed as a keyword argument.

    Returns:
        The User model instance if found, otherwise None.
    """
    # Using db.get is efficient for primary key lookups
    user = await db.get(UserModel, user_id)
    # unique() is not needed for db.get()
    return user

async def get_user_by_email(db: AsyncSession, *, email: str) -> Optional[UserModel]:
    """
    Retrieves a single user by their email address.

    Args:
        db: The AsyncSession instance.
        email: The email address of the user to retrieve.
               Must be passed as a keyword argument.

    Returns:
        The User model instance if found, otherwise None.
    """
    stmt = select(UserModel).where(UserModel.email == email)
    result = await db.execute(stmt)
    # unique() might be good practice if email constraint isn't absolutely guaranteed by DB
    return result.unique().scalar_one_or_none()

async def get_user_by_auth0_sub(db: AsyncSession, *, auth0_sub: str) -> Optional[UserModel]:
    """
    Retrieves a single user by their Auth0 subject identifier.

    Args:
        db: The AsyncSession instance.
        auth0_sub: The Auth0 subject identifier of the user to retrieve.
                   Must be passed as a keyword argument.

    Returns:
        The User model instance if found, otherwise None.
    """
    stmt = select(UserModel).where(UserModel.auth0_sub == auth0_sub)
    result = await db.execute(stmt)
    # unique() might be good practice if auth0_sub constraint isn't absolutely guaranteed by DB
    return result.unique().scalar_one_or_none()


async def get_users(
    db: AsyncSession, *, skip: int = 0, limit: int = 100
) -> List[UserModel]:
    """
    Retrieves a list of users with pagination.

    Args:
        db: The AsyncSession instance.
        skip: The number of users to skip (for pagination).
              Must be passed as a keyword argument. Defaults to 0.
        limit: The maximum number of users to return (for pagination).
               Must be passed as a keyword argument. Defaults to 100.

    Returns:
        A list of User model instances.
    """
    stmt = (
        select(UserModel)
        .offset(skip)
        .limit(limit)
        .order_by(UserModel.created_at, UserModel.id)
    )
    result = await db.execute(stmt)
    # unique() is generally not needed here unless complex relationships are loaded
    return result.scalars().all()

# --- Update ---
# Keeping update using schema for now, as it often maps well to partial updates
async def update_user(
    db: AsyncSession, *, db_user: UserModel, user_in: UserSchema.UserUpdate
) -> UserModel:
    """
    Updates an existing user's information using UserUpdate schema.

    Args:
        db: The AsyncSession instance.
        db_user: The existing User model instance to update (fetched beforehand).
                 Must be passed as a keyword argument.
        user_in: The Pydantic schema containing the fields to update.
                 Must be passed as a keyword argument.

    Returns:
        The updated User model instance.
    """
    update_data = user_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(db_user, key):
            setattr(db_user, key, value)

    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user

# --- Delete ---
async def delete_user(db: AsyncSession, *, db_user: UserModel) -> UserModel:
    """
    Deletes a user from the database.

    Args:
        db: The AsyncSession instance.
        db_user: The User model instance to delete (fetched beforehand).
                 Must be passed as a keyword argument.

    Returns:
        The deleted User model instance (now detached from the session).
    """
    await db.delete(db_user)
    await db.flush()
    return db_user
