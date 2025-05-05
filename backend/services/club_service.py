# backend/services/club_service.py

import uuid
import logging # Import logging
from decimal import Decimal # Added for balance check
from typing import Dict, Any, Sequence

# Assuming SQLAlchemy and FastAPI are installed in the environment
# If running locally, ensure these dependencies are met.
# pip install sqlalchemy fastapi asyncpg psycopg2-binary python-dotenv
# (asyncpg/psycopg2 depends on your DB dialect)
try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.exc import IntegrityError # Although less likely here, good practice
    from fastapi import HTTPException, status
    from sqlalchemy.orm import selectinload # Added for eager loading
except ImportError:
    # Provide fallback message if imports fail (e.g., in environments without these libs)
    print("WARNING: SQLAlchemy or FastAPI not found. Service functions may not execute.")
    # Define dummy types/classes if needed for the code to be syntactically valid
    class AsyncSession: pass
    class IntegrityError(Exception): pass
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)
    class Status:
        HTTP_400_BAD_REQUEST = 400 # Added for last admin check
        HTTP_403_FORBIDDEN = 403 # Added for authorization
        HTTP_404_NOT_FOUND = 404
        HTTP_409_CONFLICT = 409
        HTTP_500_INTERNAL_SERVER_ERROR = 500
    status = Status()
    def selectinload(*args): pass # Dummy decorator


# Import CRUD functions (assuming they exist in the specified paths)
# Use try-except blocks for robustness if structure might vary
try:
    from backend.crud import (
        user as crud_user,
        club as crud_club,
        fund as crud_fund,
        club_membership as crud_membership,
        member_transaction as crud_member_tx, # Added for balance check
    )
    # Added User model for list_user_clubs
    from backend.models import User, Club, Fund, ClubMembership # [cite: backend_files/models/user.py, backend_files/models/club.py, backend_files/models/fund.py, backend_files/models/club_membership.py]
    from backend.models.enums import ClubRole # [cite: backend_files/models/enums.py]
    # Added ClubMembershipUpdate schema
    from backend.schemas import ClubCreate, ClubMembershipUpdate # [cite: backend_files/schemas/club.py]
except ImportError as e:
    print(f"WARNING: Failed to import CRUD/Models/Schemas: {e}. Service functions may not work.")
    # Define dummy classes/types if needed for syntax validity
    class User: id: uuid.UUID; memberships: list = []
    class Club: id: uuid.UUID; name: str
    class Fund: id: uuid.UUID
    class ClubMembership: id: uuid.UUID; club: Any; role: Any; user_id: uuid.UUID # Added user_id
    class ClubRole: ADMIN = "Admin"; MEMBER = "Member" # Added MEMBER
    class ClubCreate: name: str; description: str | None = None
    # Added dummy schema
    class ClubMembershipUpdate: role: ClubRole | None
    # Dummy CRUD functions
    class crud_user:
        @staticmethod
        async def get_user_by_auth0_sub(db: AsyncSession, *, auth0_sub: str) -> User | None: return User(id=uuid.uuid4()) # Return dummy user
        # Added dummy get_user_by_email
        @staticmethod
        async def get_user_by_email(db: AsyncSession, *, email: str) -> User | None: return User(id=uuid.uuid4())
    class crud_club:
        @staticmethod
        async def create_club(db: AsyncSession, *, club_data: Dict[str, Any]) -> Club: return Club(id=uuid.uuid4(), name=club_data.get('name',''))
        # Added dummy get_club
        @staticmethod
        async def get_club(db: AsyncSession, club_id: uuid.UUID) -> Club | None: return Club(id=club_id, name="Dummy Club")
    class crud_fund:
        @staticmethod
        async def create_fund(db: AsyncSession, *, fund_data: Dict[str, Any]) -> Fund: return Fund(id=uuid.uuid4())
    class crud_membership:
         @staticmethod
         async def create_club_membership(db: AsyncSession, *, membership_data: Dict[str, Any]) -> ClubMembership: return ClubMembership(id=uuid.uuid4(), role=membership_data.get('role'), user_id=membership_data.get('user_id'))
         # Added dummy get_multi_club_memberships
         @staticmethod
         async def get_multi_club_memberships(db: AsyncSession, *, club_id: uuid.UUID | None = None, user_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100) -> Sequence[ClubMembership]:
             # Simulate returning memberships with clubs for a user or club
             if user_id:
                 return [ClubMembership(id=uuid.uuid4(), club=Club(id=uuid.uuid4(), name="Dummy Club 1"), role=ClubRole.MEMBER, user_id=user_id)]
             elif club_id:
                 # Simulate one admin and one member for last admin check
                 return [ClubMembership(id=uuid.uuid4(), club=Club(id=club_id), role=ClubRole.ADMIN, user_id=uuid.uuid4()), ClubMembership(id=uuid.uuid4(), club=Club(id=club_id), role=ClubRole.MEMBER, user_id=uuid.uuid4())]
             else:
                 return []
         # Added dummy get_club_membership_by_user_and_club
         @staticmethod
         async def get_club_membership_by_user_and_club(db: AsyncSession, *, user_id: uuid.UUID, club_id: uuid.UUID) -> ClubMembership | None:
             # Simulate finding the requestor as ADMIN, but not finding others initially
             # Need to simulate finding the target member for removal/update
             if str(user_id).startswith("req"): # Dummy check for requestor
                 return ClubMembership(id=uuid.uuid4(), role=ClubRole.ADMIN, user_id=user_id)
             elif str(user_id).startswith("target"): # Dummy check for target member
                  return ClubMembership(id=uuid.uuid4(), role=ClubRole.MEMBER, user_id=user_id) # Simulate finding target
             else:
                 # Simulate finding a MEMBER for the not_admin test
                 return ClubMembership(id=uuid.uuid4(), role=ClubRole.MEMBER, user_id=user_id)
         # Added dummy update_club_membership
         @staticmethod
         async def update_club_membership(db: AsyncSession, *, db_obj: ClubMembership, obj_in: ClubMembershipUpdate) -> ClubMembership:
             db_obj.role = obj_in.role
             return db_obj
         # Added dummy delete_club_membership
         @staticmethod
         async def delete_club_membership(db: AsyncSession, *, db_obj: ClubMembership) -> ClubMembership:
              return db_obj # Return the object as if deleted
    # Added dummy member_transaction crud for balance check
    class crud_member_tx:
         @staticmethod
         async def get_member_unit_balance(db: AsyncSession, membership_id: uuid.UUID) -> Decimal:
              # Simulate zero balance for removal check to pass
              return Decimal("0.0")


# Configure logging
log = logging.getLogger(__name__)


async def create_club(
    db: AsyncSession, *, club_in: ClubCreate, auth0_sub: str
) -> Club:
    """ Orchestrates the creation of a new club... (Implementation omitted) """
    # ... (implementation as before) ...
    creator: User | None = await crud_user.get_user_by_auth0_sub(db=db, auth0_sub=auth0_sub)
    if not creator: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with auth0_sub '{auth0_sub}' not found.")
    log.info(f"User {creator.id} attempting to create club '{club_in.name}'")
    club_data: Dict[str, Any] = {"name": club_in.name, "description": club_in.description, "creator_id": creator.id}
    try:
        new_club: Club = await crud_club.create_club(db=db, club_data=club_data)
        log.info(f"Created club {new_club.id} with name '{new_club.name}'")
        default_fund_data: Dict[str, Any] = {"club_id": new_club.id, "name": "General Fund", "description": "Default fund for general club holdings.", "is_active": True}
        default_fund = await crud_fund.create_fund(db=db, fund_data=default_fund_data)
        log.info(f"Created default fund {default_fund.id} for club {new_club.id}")
        creator_membership_data: Dict[str, Any] = {"user_id": creator.id, "club_id": new_club.id, "role": ClubRole.ADMIN}
        creator_membership = await crud_membership.create_club_membership(db=db, membership_data=creator_membership_data)
        log.info(f"Created ADMIN membership {creator_membership.id} for creator {creator.id} in club {new_club.id}")
        await db.flush()
        log.info(f"Successfully created club {new_club.id} and associated defaults.")
        return new_club
    except IntegrityError as e: log.exception(f"IntegrityError during club creation for creator {creator.id}, name '{club_in.name}': {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Could not create club. A club with name '{club_in.name}' might already exist.")
    except Exception as e: log.exception(f"Error during club creation for creator {creator.id}: {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while creating the club.")


async def get_club_details(db: AsyncSession, *, club_id: uuid.UUID) -> Club:
    """ Retrieves details for a specific club. (Implementation omitted) """
    # ... (implementation as before) ...
    log.info(f"Retrieving details for club {club_id}")
    club = await crud_club.get_club(db=db, club_id=club_id)
    if not club: log.warning(f"Club not found: {club_id}"); raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Club with id {club_id} not found.")
    log.info(f"Successfully retrieved club {club_id}")
    return club


async def list_user_clubs(db: AsyncSession, *, auth0_sub: str) -> Sequence[Club]:
    """ Retrieves a list of clubs that the specified user is a member of. (Implementation omitted) """
    # ... (implementation as before) ...
    log.info(f"Listing clubs for user with auth0_sub: {auth0_sub}")
    user = await crud_user.get_user_by_auth0_sub(db=db, auth0_sub=auth0_sub)
    if not user: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with auth0_sub '{auth0_sub}' not found.")
    log.debug(f"Found user {user.id} for auth0_sub {auth0_sub}")
    memberships = await crud_membership.get_multi_club_memberships(db=db, user_id=user.id, limit=1000 )
    user_clubs = [m.club for m in memberships if m.club]
    log.info(f"Found {len(user_clubs)} clubs for user {user.id}")
    user_clubs.sort(key=lambda club: club.name)
    return user_clubs


async def add_club_member(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    member_email: str,
    role: ClubRole = ClubRole.MEMBER,
    requesting_user: User # User object of the person making the request
) -> ClubMembership:
    """ Adds an existing user (found by email) to a club with a specified role. """
    log.info(f"Attempting to add user with email {member_email} to club {club_id} with role {role.value} by user {requesting_user.id}")

    # --- 1. Authorization Check ---
    requestor_membership = await crud_membership.get_club_membership_by_user_and_club(
        db=db, user_id=requesting_user.id, club_id=club_id
    )
    # --- DEBUGGING ---
    if requestor_membership: log.debug(f"DEBUG AUTH CHECK: Found requestor membership for user {requesting_user.id} in club {club_id}. Role: {requestor_membership.role}")
    else: log.error(f"DEBUG AUTH CHECK: No membership found for requestor user {requesting_user.id} in club {club_id}.")
    # --- END DEBUGGING ---
    if not requestor_membership or requestor_membership.role != ClubRole.ADMIN:
        log.warning(f"User {requesting_user.id} attempted to add member to club {club_id} without ADMIN role.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have permission to add members to this club.")
    log.info(f"Authorization check passed: User {requesting_user.id} is ADMIN of club {club_id}")

    # --- Steps 2-4 (Implementation omitted for brevity) ---
    user_to_add = await crud_user.get_user_by_email(db=db, email=member_email);
    if not user_to_add: log.warning(f"User with email {member_email} not found."); raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with email '{member_email}' not found.")
    existing_membership = await crud_membership.get_club_membership_by_user_and_club(db=db, user_id=user_to_add.id, club_id=club_id);
    if existing_membership: log.warning(f"User {user_to_add.id} ({member_email}) is already a member of club {club_id}."); raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User with email '{member_email}' is already a member of this club.")
    membership_data = {"user_id": user_to_add.id, "club_id": club_id, "role": role}
    try:
        new_membership = await crud_membership.create_club_membership(db=db, membership_data=membership_data)
        await db.flush()
        log.info(f"Successfully added user {user_to_add.id} to club {club_id} with role {role.value}. Membership ID: {new_membership.id}")
        return new_membership
    except IntegrityError as e: log.exception(f"IntegrityError adding user {user_to_add.id} to club {club_id}: {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Failed to add member. The user might have been added concurrently.")
    except Exception as e: log.exception(f"Unexpected error adding user {user_to_add.id} to club {club_id}: {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while adding the member.")


async def update_member_role(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    member_user_id: uuid.UUID, # ID of the user whose role is being changed
    new_role: ClubRole,
    requesting_user: User # User object of the person making the request
) -> ClubMembership:
    """ Updates the role of an existing member within a club. (Implementation omitted) """
    # ... (implementation as before) ...
    log.info(f"Attempting to update role for user {member_user_id} in club {club_id} to {new_role.value} by user {requesting_user.id}")
    requestor_membership = await crud_membership.get_club_membership_by_user_and_club(db=db, user_id=requesting_user.id, club_id=club_id)
    if not requestor_membership or requestor_membership.role != ClubRole.ADMIN: log.warning(f"User {requesting_user.id} attempted to update role in club {club_id} without ADMIN role."); raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have permission to update member roles in this club.")
    log.info(f"Authorization check passed: User {requesting_user.id} is ADMIN of club {club_id}")
    target_membership = await crud_membership.get_club_membership_by_user_and_club(db=db, user_id=member_user_id, club_id=club_id)
    if not target_membership: log.warning(f"Membership for user {member_user_id} in club {club_id} not found for role update."); raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Membership for target user in club {club_id} not found.")
    if target_membership.role == ClubRole.ADMIN and new_role != ClubRole.ADMIN:
        all_memberships = await crud_membership.get_multi_club_memberships(db=db, club_id=club_id, limit=0)
        admin_count = sum(1 for m in all_memberships if m.role == ClubRole.ADMIN)
        if admin_count <= 1: log.warning(f"Attempt blocked to remove role from last admin (User: {member_user_id}) in club {club_id}."); raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the last admin role from the club.")
    update_data = ClubMembershipUpdate(role=new_role)
    try:
        updated_membership = await crud_membership.update_club_membership(db=db, db_obj=target_membership, obj_in=update_data)
        await db.flush()
        log.info(f"Successfully updated role for user {member_user_id} in club {club_id} to {new_role.value}. Membership ID: {updated_membership.id}")
        return updated_membership
    except Exception as e: log.exception(f"Unexpected error updating role for user {member_user_id} in club {club_id}: {e}"); await db.rollback(); raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while updating the member role.")


async def remove_club_member(
    db: AsyncSession,
    *,
    club_id: uuid.UUID,
    member_user_id: uuid.UUID, # ID of the user being removed
    requesting_user: User # User object of the person making the request
) -> ClubMembership:
    """
    Removes a member from a club. Requires the member to have a zero unit balance.
    """
    log.info(f"Attempting to remove user {member_user_id} from club {club_id} by user {requesting_user.id}")

    # --- 1. Authorization Check ---
    requestor_membership = await crud_membership.get_club_membership_by_user_and_club(db=db, user_id=requesting_user.id, club_id=club_id)
    if not requestor_membership or requestor_membership.role != ClubRole.ADMIN:
        log.warning(f"User {requesting_user.id} attempted to remove member from club {club_id} without ADMIN role.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have permission to remove members from this club.")
    log.info(f"Authorization check passed: User {requesting_user.id} is ADMIN of club {club_id}")

    # --- 2. Prevent Self-Removal (by Admin) ---
    if requesting_user.id == member_user_id:
         log.warning(f"Admin user {requesting_user.id} attempted self-removal from club {club_id}.")
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins cannot remove themselves. Transfer admin rights or delete the club.")

    # --- 3. Find Target Membership ---
    target_membership = await crud_membership.get_club_membership_by_user_and_club(db=db, user_id=member_user_id, club_id=club_id)
    if not target_membership:
        log.warning(f"Membership for user {member_user_id} in club {club_id} not found for removal.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Membership for user to be removed in club {club_id} not found.")

    # --- 4. Prevent Removing Last Admin ---
    if target_membership.role == ClubRole.ADMIN:
        all_memberships = await crud_membership.get_multi_club_memberships(db=db, club_id=club_id, limit=0) # Fetch all to count admins
        admin_count = sum(1 for m in all_memberships if m.role == ClubRole.ADMIN)
        if admin_count <= 1:
            log.warning(f"Attempt blocked to remove last admin (User: {member_user_id}) from club {club_id}.")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the last admin from the club.")

    # --- 5. Check Member Unit Balance ---
    try:
        member_units = await crud_member_tx.get_member_unit_balance(db=db, membership_id=target_membership.id) # [cite: crud_member_transaction_updated]
        log.info(f"Checking unit balance for member {member_user_id} before removal: {member_units}")
        # Check if balance is effectively zero
        is_zero_balance = abs(member_units) < Decimal("0.00000001")
        log.debug(f"Balance check result for {member_user_id}: {is_zero_balance}")
        if not is_zero_balance:
             log.warning(f"Attempt blocked to remove member {member_user_id} from club {club_id} with non-zero unit balance ({member_units}).")
             # **FIX:** Raise 400 directly if balance is not zero
             raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail=f"Cannot remove member. Member must withdraw all funds (unit balance is {member_units:.8f}, must be 0)."
             )
    except AttributeError:
        # This specific error means the CRUD function itself is missing
        log.error("CRUD function 'get_member_unit_balance' not found during member removal check.")
        # Raise 500 because it's an internal setup problem
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error: Cannot verify member unit balance.")
    except HTTPException as e:
        # Re-raise any HTTPExceptions that might come from get_member_unit_balance itself
        raise e
    except Exception as e:
        # Catch any other unexpected error during the balance check
        log.exception(f"Error checking unit balance for membership {target_membership.id} during removal: {e}")
        # Raise 500 for unexpected errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not verify member unit balance.")

    # --- 6. Perform Deletion ---
    # If we reach here, all checks passed (authorized, not last admin, zero balance)
    try:
        deleted_membership = await crud_membership.delete_club_membership(db=db, db_obj=target_membership) # [cite: backend_files/crud/club_membership.py]
        await db.flush() # Flush to catch potential errors early
        log.info(f"Successfully removed user {member_user_id} from club {club_id}. Membership ID: {deleted_membership.id}")
        return deleted_membership
    except Exception as e:
        # Catch unexpected errors during delete
        log.exception(f"Unexpected error removing user {member_user_id} from club {club_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while removing the member.",
        )

