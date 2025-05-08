# backend/api/v1/endpoints/users.py

import uuid
import logging
from typing import Any # Added Any for dummy types

# Assuming FastAPI and related libraries are installed
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession # Not strictly needed here, but good practice

# Import dependencies, schemas, models
from backend.api.dependencies import get_current_active_user # Import the core dependency
from backend.schemas import UserRead # Import the response schema
from backend.models import User # Import the User model for type hinting


# Configure logging
log = logging.getLogger(__name__)

# Create router instance
router = APIRouter()


@router.get(
    "/me", # Path relative to the prefix defined in api/v1/__init__.py (/users)
    response_model=UserRead, # Specify the response schema
    summary="Get Current User",
    description="Retrieves the profile information for the currently authenticated user.",
)
async def read_users_me(
    current_user: User = Depends(get_current_active_user) # Inject the dependency
):
    """
    API endpoint to get the current authenticated user's details.
    The dependency `get_current_active_user` handles authentication
    and fetching/creating the user record.
    """
    log.info(f"Request received for /users/me by user {current_user.id} (email: {current_user.email}, auth0_sub: {current_user.auth0_sub})")
    # The dependency already fetched the user object.
    # FastAPI will automatically validate and serialize it using the UserRead model.
    log.info(f"Returning user data for ID: {current_user.id}")
    return current_user

# --- Add other user-related endpoints here if needed ---
# E.g., PUT /users/me for profile updates (requires service function)
# E.g., DELETE /users/me (requires service function and careful consideration)

