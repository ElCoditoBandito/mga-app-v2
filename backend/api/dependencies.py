# backend/api/dependencies.py

import logging
import uuid
import os # Added for env vars
import json # Added for JWKS parsing (though httpx handles it)
from typing import Annotated, Any, Optional, Dict, List # Added Optional, Dict, List
from datetime import datetime, timedelta, timezone # Added timedelta for cache check

# Third-party imports for Auth0 validation
import httpx # Added for async HTTP requests
from jose import jwt, JWTError # Added JWT handling
from jose.exceptions import ExpiredSignatureError, JWKError # Added specific JOSE errors
from pydantic import BaseModel # Added for JWT Payload model
from dotenv import load_dotenv # Added to load env vars

# Assuming FastAPI and related libraries are installed
from fastapi import Depends, HTTPException, status, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials # Use HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

# Import necessary services, models, and session dependency
from backend.core.session import get_db_session
from backend.services import user_service
from backend.models import User, ClubMembership
from backend.models.enums import ClubRole
from backend.crud import club_membership as crud_membership


# --- Logging Configuration ---
log = logging.getLogger(__name__)

# --- Auth0 Configuration ---
load_dotenv() # Ensure environment variables are loaded

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ALGORITHMS = ["RS256"]

# Validate required environment variables
if not AUTH0_DOMAIN:
    # Use log.error and raise RuntimeError for critical config missing at startup
    log.error("AUTH0_DOMAIN environment variable not set")
    raise RuntimeError("AUTH0_DOMAIN environment variable not set")
if not AUTH0_AUDIENCE:
    log.error("AUTH0_AUDIENCE environment variable not set")
    raise RuntimeError("AUTH0_AUDIENCE environment variable not set")

# --- JWKS Caching ---
jwks_cache: Dict[str, Any] = {}
jwks_last_updated: Optional[datetime] = None
JWKS_CACHE_TTL = timedelta(hours=24) # Cache JWKS for 24 hours

# --- Pydantic Model for JWT Payload ---
class JWTPayload(BaseModel):
    """Model for validated JWT payload data."""
    sub: str  # Auth0 user ID (e.g., "auth0|123456789")
    iss: str
    aud: List[str] | str # Audience can sometimes be a string or list
    iat: int
    exp: int
    azp: Optional[str] = None
    scope: Optional[str] = None
    permissions: Optional[List[str]] = None
    # Add email if it's expected directly in the token (configure in Auth0 rule/action)
    email: Optional[str] = None # Make optional, might not always be present

# --- JWKS Fetching Function ---
async def get_jwks() -> Dict[str, Any]:
    """
    Fetches the JSON Web Key Set (JWKS) from Auth0.
    Caches the result to avoid unnecessary HTTP requests.
    """
    global jwks_cache, jwks_last_updated
    now = datetime.now(timezone.utc) # Use timezone-aware datetime

    # Check cache validity
    if jwks_cache and jwks_last_updated and (now - jwks_last_updated < JWKS_CACHE_TTL):
        log.debug("Using cached JWKS.")
        return jwks_cache

    # Fetch JWKS from Auth0
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    log.info(f"Fetching JWKS from {jwks_url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url, timeout=10.0) # Add timeout
            response.raise_for_status() # Raise HTTP errors
            jwks_cache = response.json()
            jwks_last_updated = now
            log.info("Successfully fetched and cached JWKS.")
            return jwks_cache
    except httpx.RequestError as e:
        log.exception(f"Error fetching JWKS: {e}. Using potentially stale cache if available.")
        # If cache exists, return it, otherwise raise error
        if jwks_cache:
            return jwks_cache
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Could not fetch authentication keys from provider.",
            ) from e
    except Exception as e:
         log.exception(f"Unexpected error fetching JWKS: {e}")
         if jwks_cache:
             return jwks_cache
         else:
             raise HTTPException(
                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                 detail="An internal error occurred while fetching authentication keys.",
             ) from e


# --- Token Verification Function ---
async def verify_token(token: str) -> JWTPayload:
    """
    Verifies the JWT token using the JWKS from Auth0.
    Returns the decoded payload if valid.
    Raises HTTPException if token is invalid.
    """
    log.debug("Attempting to verify token...")
    try:
        jwks = await get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        if "kid" not in unverified_header:
             log.warning("Token header missing 'kid'.")
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header", headers={"WWW-Authenticate": "Bearer"})

        for key in jwks.get("keys", []):
            if key.get("kid") == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            log.warning(f"Unable to find appropriate key for kid: {unverified_header.get('kid')}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to find appropriate key", headers={"WWW-Authenticate": "Bearer"})

        log.debug("Decoding token...")
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE, # Verify audience matches your API identifier
            issuer=f"https://{AUTH0_DOMAIN}/", # Verify issuer matches your Auth0 domain
        )
        log.debug("Token decoded successfully.")

        # Validate payload structure using Pydantic model
        # This also extracts relevant fields like sub and email if present
        validated_payload = JWTPayload(**payload)
        log.debug(f"Token payload validated for sub: {validated_payload.sub}")
        return validated_payload

    except ExpiredSignatureError:
        log.warning("Token validation failed: Expired signature.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired", headers={"WWW-Authenticate": "Bearer"})
    except JWTError as e:
        log.warning(f"Token validation failed: JWTError - {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})
    except JWKError as e:
         log.warning(f"Token validation failed: JWKError - {e}")
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature", headers={"WWW-Authenticate": "Bearer"})
    except Exception as e:
        log.exception(f"Unexpected error during token verification: {e}") # Log full exception
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})


# --- FastAPI Security Scheme ---
# Use HTTPBearer which expects "Bearer <token>"
token_auth_scheme = HTTPBearer(auto_error=True) # auto_error=True raises 401 automatically if header is missing/malformed

# --- Current User Dependency ---
async def get_current_active_user(
    # Use HTTPBearer dependency
    token_creds: HTTPAuthorizationCredentials = Depends(token_auth_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    FastAPI dependency to:
    1. Verify the Auth0 Access Token from the Authorization header.
    2. Extract user claims (sub, email).
    3. Get or create the corresponding user in the local database.
    4. Check if the local user is active.
    Returns the active local User model instance.
    """
    log.debug("Attempting to get current active user...")
    token = token_creds.credentials # Extract token string

    try:
        # Verify the token using the actual verification function
        payload: JWTPayload = await verify_token(token)
        log.debug(f"Token verified for sub: {payload.sub}")

        auth0_sub = payload.sub
        # --- Get Email ---
        # Prioritize email from token payload if available (more direct)
        # Otherwise, you might need another way (e.g., call Auth0 /userinfo endpoint - more complex)
        email = payload.email
        if not email:
            # If email is not in the token, you MUST configure Auth0
            # (e.g., using Actions/Rules) to add it, or fetch it separately.
            # Raising an error here as email is required by get_or_create_user_by_auth0.
            log.error(f"Email claim missing from validated token for sub: {auth0_sub}. Check Auth0 Action/Rule.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User email could not be determined from token.")
        # --- End Get Email ---

        # Get or create local user based on validated Auth0 sub and email
        user = await user_service.get_or_create_user_by_auth0(
            db=db, auth0_sub=auth0_sub, email=email
        ) # [cite: backend/services/user_service.py]

        if not user.is_active:
            log.warning(f"Authentication successful, but user {user.id} ({user.email}) is inactive.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user.")

        log.info(f"Authenticated active user: {user.id} ({getattr(user, 'email', 'N/A')})")
        return user

    except HTTPException as e:
        # Re-raise HTTPExceptions raised by verify_token or user_service
        log.warning(f"Authentication/User fetch failed: {e.detail} (Status: {e.status_code})")
        # Ensure WWW-Authenticate header is set for 401 errors from verify_token
        headers = e.headers if e.status_code == 401 else None
        raise HTTPException(status_code=e.status_code, detail=e.detail, headers=headers) from e
    except Exception as e:
        # Catch any other unexpected errors during the process
        log.exception(f"Unexpected error during get_current_active_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user authentication."
        )


# --- Authorization Dependencies ---

async def require_club_admin(
    # Use older style for path parameter as well if preferred, or keep Annotated
    club_id: uuid.UUID = Path(..., title="The ID of the club to check admin status for"),
    # Use older style for dependencies
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> ClubMembership: # Return the membership object for potential use
    """
    FastAPI dependency to ensure the current user is an ADMIN of the specified club.
    (Implementation unchanged)
    """
    log.debug(f"Checking ADMIN status for user {current_user.id} in club {club_id}")
    membership = await crud_membership.get_club_membership_by_user_and_club(
        db=db, user_id=current_user.id, club_id=club_id
    ) # [cite: backend_files/crud/club_membership.py]

    if not membership:
        log.warning(f"User {current_user.id} is not a member of club {club_id}.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Or 403? 404 seems appropriate if the link doesn't exist
            detail=f"User is not a member of club {club_id}."
        )

    if membership.role != ClubRole.ADMIN: # [cite: backend_files/models/club_membership.py, backend_files/models/enums.py]
        log.warning(f"User {current_user.id} is not an ADMIN of club {club_id} (Role: {membership.role}).")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have ADMIN privileges for this club."
        )

    log.debug(f"User {current_user.id} confirmed as ADMIN for club {club_id}")
    return membership

# --- Club Member Dependency ---
async def require_club_member(
    club_id: uuid.UUID = Path(..., title="The ID of the club to check membership status for"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
) -> ClubMembership:
    """Dependency to ensure the user is at least a MEMBER of the club."""
    log.debug(f"Checking MEMBER status for user {current_user.id} in club {club_id}")
    membership = await crud_membership.get_club_membership_by_user_and_club(
        db=db, user_id=current_user.id, club_id=club_id
    )
    if not membership:
        log.warning(f"User {current_user.id} is not a member of club {club_id}.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # 403 is generally better for authorization failures
            detail=f"User is not authorized to access this club."
        )
    # Add check for specific roles if needed (e.g., MEMBER or ADMIN)
    # if membership.role not in [ClubRole.ADMIN, ClubRole.MEMBER]: ...
    log.debug(f"User {current_user.id} confirmed as member of club {club_id}")
    return membership

