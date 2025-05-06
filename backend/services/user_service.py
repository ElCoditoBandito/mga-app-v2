# backend/services/user_service.py

import uuid
import logging # Import logging
from typing import Dict, Any

# Assuming SQLAlchemy and FastAPI are installed in the environment
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

# Import CRUD functions and Models
from backend.crud import user as crud_user
from backend.models import User # [cite: backend_files/models/user.py]

# Configure logging for this module
log = logging.getLogger(__name__)


async def get_or_create_user_by_auth0(
    db: AsyncSession, *, auth0_sub: str, email: str
) -> User:
    """
    Retrieves a user by their Auth0 subject ID, creating them if they don't exist.

    This is typically called after successful authentication when the API receives
    the user's auth0_sub and email from the validated token.

    Args:
        db: The AsyncSession instance.
        auth0_sub: The unique subject identifier from Auth0.
        email: The user's email address (from Auth0 token).

    Returns:
        The existing or newly created User model instance.

    Raises:
        HTTPException: If user creation fails due to a database conflict (e.g., email exists
                       but associated with a different auth0_sub - indicates data inconsistency).
        HTTPException: For other unexpected database errors during creation.
    """
    # 1. Attempt to find the user by auth0_sub
    user = await crud_user.get_user_by_auth0_sub(db=db, auth0_sub=auth0_sub) # [cite: backend_files/crud/user.py]

    if user:
        log.info(f"Found existing user for auth0_sub: {auth0_sub}")
        return user
    else:
        # 2. User not found, attempt to create them
        log.info(f"User not found for auth0_sub: {auth0_sub}. Attempting creation with email: {email}.")
        user_data = {
            "auth0_sub": auth0_sub,
            "email": email,
            # is_active defaults to True in CRUD/model [cite: backend_files/crud/user.py, backend_files/models/user.py]
        }
        try:
            new_user = await crud_user.create_user(db=db, user_data=user_data) # [cite: backend_files/crud/user.py]
            log.info(f"Successfully created new user (ID: {new_user.id}) for auth0_sub: {auth0_sub}") # [cite: backend_files/models/user.py]
            return new_user
        except IntegrityError as e:
            # This likely means the email already exists, but the auth0_sub didn't match.
            # This points to a potential data inconsistency or an edge case.
            # Use log.exception to include stack trace for errors
            log.exception(f"IntegrityError creating user for auth0_sub {auth0_sub}, email {email}: {e}")
            await db.rollback() # Rollback the specific failed operation
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Could not create user. Email '{email}' might already be associated with another account.",
            )
        except Exception as e:
            # Catch other unexpected errors during creation
            log.exception(f"Unexpected error creating user for auth0_sub {auth0_sub}: {e}")
            await db.rollback() # Rollback on any other error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while creating the user.",
            )

