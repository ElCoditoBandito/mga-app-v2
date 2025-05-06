# backend/api/v1/endpoints/clubs.py

import uuid
import logging
from typing import List, Any, Sequence
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field, conlist

# Import dependencies, schemas, services, models
from backend.api.dependencies import (
    get_db_session, get_current_active_user,
    require_club_admin, require_club_member
)
from backend.schemas import (
    ClubCreate, ClubRead, ClubReadBasic, ClubPortfolio, ClubUpdate,
    ClubMembershipRead, ClubMembershipUpdate, ClubMembershipReadBasicUser,
    MemberTransactionRead, MemberTransactionCreate, MemberTransactionReadBasic, # Added Basic Read
    UnitValueHistoryRead,
    FundRead, FundReadBasic, FundUpdate,
    FundSplitRead, FundSplitItem
)
from backend.services.reporting_service import ClubPerformanceData, MemberStatementData
from backend.services import (
    club_service, reporting_service, accounting_service,
    fund_service, fund_split_service # Added new services
)
from backend.models import User, Club, ClubMembership, MemberTransaction, UnitValueHistory, Fund, FundSplit
from backend.models.enums import MemberTransactionType, ClubRole
# Import specific CRUD needed
from backend.crud import club as crud_club, fund as crud_fund, member_transaction as crud_member_tx, club_membership as crud_membership


# Configure logging
log = logging.getLogger(__name__)

# Create router instance
router = APIRouter()

# --- Request Body Schema Definitions ---
class MemberAddSchema(BaseModel):
    member_email: EmailStr
    role: ClubRole = ClubRole.MEMBER

class MemberRoleUpdateSchema(BaseModel):
    new_role: ClubRole

class MemberTransactionCreateApi(BaseModel):
    user_id: uuid.UUID = Field(..., description="The ID of the member this transaction belongs to")
    amount: Decimal = Field(..., gt=Decimal(0), max_digits=15, decimal_places=2)
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    notes: str | None = None

class NavCalculationRequest(BaseModel):
    valuation_date: date

# --- Club Endpoints ---

@router.post("", response_model=ClubRead, status_code=status.HTTP_201_CREATED, summary="Create New Club", description="Creates a new investment club...", dependencies=[Depends(get_current_active_user)])
async def create_new_club(club_in: ClubCreate, db: AsyncSession = Depends(get_db_session), current_user: User = Depends(get_current_active_user)):
    log.info(f"Received request to create club '{club_in.name}' by user {current_user.id}")
    try:
        auth0_sub = getattr(current_user, 'auth0_sub', None)
        if not auth0_sub: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error: User identity missing.")
        new_club = await club_service.create_club(db=db, club_in=club_in, auth0_sub=auth0_sub)
        club_name = getattr(new_club, 'name', 'Unknown'); club_id = getattr(new_club, 'id', 'Unknown')
        log.info(f"Club '{club_name}' created successfully with ID {club_id}")
        return new_club
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error creating club '{getattr(club_in, 'name', 'Unknown')}' for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while creating the club.")


@router.get("", response_model=List[ClubReadBasic], summary="List User's Clubs", description="Retrieves a list of all investment clubs...", dependencies=[Depends(get_current_active_user)])
async def get_user_clubs(db: AsyncSession = Depends(get_db_session), current_user: User = Depends(get_current_active_user)):
    log.info(f"Received request to list clubs for user {current_user.id}")
    try:
        auth0_sub = getattr(current_user, 'auth0_sub', None)
        if not auth0_sub: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error: User identity missing.")
        user_clubs = await club_service.list_user_clubs(db=db, auth0_sub=auth0_sub)
        log.info(f"Found {len(user_clubs)} clubs for user {current_user.id}")
        return user_clubs
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error listing clubs for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while listing clubs.")


@router.get("/{club_id}", response_model=ClubRead, summary="Get Club Details", description="Retrieves detailed information about a specific investment club.", dependencies=[Depends(require_club_member)])
async def get_single_club(club_id: uuid.UUID = Path(...), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request for details of club {club_id}")
    try:
        # Service function handles fetching details
        club = await club_service.get_club_details(db=db, club_id=club_id)
        log.info(f"Successfully retrieved details for club {club_id}")
        return club
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error retrieving club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while retrieving club details.")


@router.put("/{club_id}", response_model=ClubRead, summary="Update Club Details", description="Updates the name or description of a club. Requires ADMIN privileges.", dependencies=[Depends(require_club_admin)])
async def update_club_details(club_id: uuid.UUID = Path(...), club_update_data: ClubUpdate = Body(...), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request to update club {club_id}")
    db_club = await crud_club.get_club(db=db, club_id=club_id)
    if not db_club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Club {club_id} not found.")
    try:
        updated_club = await crud_club.update_club(db=db, db_obj=db_club, obj_in=club_update_data)
        log.info(f"Successfully updated club {club_id}")
        return updated_club
    except Exception as e:
        log.exception(f"Unexpected error updating club {club_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while updating the club.")


@router.get("/{club_id}/portfolio", response_model=ClubPortfolio, summary="Get Club Portfolio Report", description="Retrieves an aggregated portfolio report...", dependencies=[Depends(require_club_member)])
async def get_club_portfolio(club_id: uuid.UUID = Path(...), valuation_date: date = Query(default_factory=date.today), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request for portfolio report for club {club_id} on {valuation_date}")
    try:
        report_data = await reporting_service.get_club_portfolio_report(db=db, club_id=club_id, valuation_date=valuation_date)
        log.info(f"Successfully generated portfolio report for club {club_id}")
        return report_data
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error generating portfolio report for club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while generating the portfolio report.")


@router.get("/{club_id}/performance", response_model=ClubPerformanceData, summary="Get Club Performance Report", description="Retrieves the Holding Period Return (HPR)...", dependencies=[Depends(require_club_member)])
async def get_club_performance_report(club_id: uuid.UUID = Path(...), start_date: date = Query(...), end_date: date = Query(...), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request for performance report for club {club_id} from {start_date} to {end_date}")
    try:
        performance_data = await reporting_service.get_club_performance(db=db, club_id=club_id, start_date=start_date, end_date=end_date)
        log.info(f"Successfully generated performance report for club {club_id}")
        return performance_data
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error generating performance report for club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while generating the performance report.")


# --- Club Membership Endpoints ---

@router.get("/{club_id}/members", response_model=List[ClubMembershipRead], summary="List Club Members", description="Retrieves a list of all members...", dependencies=[Depends(require_club_member)])
async def list_club_members(club_id: uuid.UUID = Path(...), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request to list members for club {club_id}")
    try:
        memberships = await crud_membership.get_multi_club_memberships(db=db, club_id=club_id, limit=0) # limit=0 for all
        log.info(f"Found {len(memberships)} members for club {club_id}")
        return memberships
    except Exception as e:
        log.exception(f"Unexpected error listing members for club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while listing members.")


@router.post("/{club_id}/members", response_model=ClubMembershipRead, status_code=status.HTTP_201_CREATED, summary="Add Member to Club", description="Adds an existing user...", dependencies=[Depends(require_club_admin)])
async def add_member(club_id: uuid.UUID = Path(...), member_data: MemberAddSchema = Body(...), db: AsyncSession = Depends(get_db_session), current_user: User = Depends(get_current_active_user)):
    log.info(f"Received request to add member '{member_data.member_email}' to club {club_id} by admin {current_user.id}")
    try:
        new_membership = await club_service.add_club_member(db=db, club_id=club_id, member_email=member_data.member_email, role=member_data.role, requesting_user=current_user)
        log.info(f"Successfully added membership {new_membership.id} for email {member_data.member_email} to club {club_id}")
        return new_membership
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error adding member {member_data.member_email} to club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while adding the member.")


@router.put("/{club_id}/members/{user_id}", response_model=ClubMembershipRead, summary="Update Member Role", description="Updates the role of a specific member...", dependencies=[Depends(require_club_admin)])
async def update_member_role_endpoint(club_id: uuid.UUID = Path(...), user_id: uuid.UUID = Path(...), role_update: MemberRoleUpdateSchema = Body(...), db: AsyncSession = Depends(get_db_session), current_user: User = Depends(get_current_active_user)):
    log.info(f"Received request to update role for user {user_id} in club {club_id} to {role_update.new_role} by admin {current_user.id}")
    try:
        updated_membership = await club_service.update_member_role(db=db, club_id=club_id, member_user_id=user_id, new_role=role_update.new_role, requesting_user=current_user)
        log.info(f"Successfully updated role for user {user_id} in club {club_id} to {role_update.new_role}")
        return updated_membership
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error updating role for user {user_id} in club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while updating the member role.")


@router.delete("/{club_id}/members/{user_id}", response_model=ClubMembershipRead, summary="Remove Member from Club", description="Removes a member from the specified club...", dependencies=[Depends(require_club_admin)])
async def remove_member(club_id: uuid.UUID = Path(...), user_id: uuid.UUID = Path(...), db: AsyncSession = Depends(get_db_session), current_user: User = Depends(get_current_active_user)):
    log.info(f"Received request to remove user {user_id} from club {club_id} by admin {current_user.id}")
    try:
        deleted_membership = await club_service.remove_club_member(db=db, club_id=club_id, member_user_id=user_id, requesting_user=current_user)
        log.info(f"Successfully removed membership {deleted_membership.id} (User: {user_id}) from club {club_id}")
        return deleted_membership
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error removing user {user_id} from club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while removing the member.")


# --- Fund Endpoints ---

@router.get("/{club_id}/funds", response_model=List[FundReadBasic], summary="List Club Funds", description="Retrieves a list of all funds...", dependencies=[Depends(require_club_member)])
async def list_club_funds(club_id: uuid.UUID = Path(...), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request to list funds for club {club_id}")
    try:
        funds = await crud_fund.get_multi_funds(db=db, club_id=club_id, limit=0) # limit=0 for all
        log.info(f"Found {len(funds)} funds for club {club_id}")
        return funds
    except Exception as e:
        log.exception(f"Unexpected error listing funds for club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while listing funds.")


@router.put("/{club_id}/funds/{fund_id}", response_model=FundRead, summary="Update Fund Details", description="Updates the name, description, or active status...", dependencies=[Depends(require_club_admin)])
async def update_fund_endpoint(club_id: uuid.UUID = Path(...), fund_id: uuid.UUID = Path(...), fund_update_data: FundUpdate = Body(...), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request to update fund {fund_id} in club {club_id}")
    fund = await crud_fund.get_fund(db=db, fund_id=fund_id)
    if not fund or fund.club_id != club_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Fund {fund_id} not found in club {club_id}")
    try:
        updated_fund = await fund_service.update_fund_details(db=db, fund_id=fund_id, fund_in=fund_update_data)
        log.info(f"Successfully updated fund {fund_id}")
        return updated_fund
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error updating fund {fund_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while updating the fund.")


# --- Fund Split Endpoints ---

@router.get("/{club_id}/fund-splits", response_model=List[FundSplitRead], summary="Get Fund Splits", description="Retrieves the current fund split configuration...", dependencies=[Depends(require_club_member)])
async def get_fund_splits_endpoint(club_id: uuid.UUID = Path(...), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request to get fund splits for club {club_id}")
    try:
        splits = await fund_split_service.get_fund_splits_for_club(db=db, club_id=club_id)
        log.info(f"Retrieved {len(splits)} fund splits for club {club_id}")
        return splits
    except Exception as e:
        log.exception(f"Unexpected error getting fund splits for club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while retrieving fund splits.")


@router.put("/{club_id}/fund-splits", response_model=List[FundSplitRead], summary="Set Fund Splits", description="Sets or replaces the entire fund split configuration...", dependencies=[Depends(require_club_admin)])
async def set_fund_splits_endpoint(club_id: uuid.UUID = Path(...), fund_splits_in: List[FundSplitItem] = Body(...), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request to set {len(fund_splits_in)} fund splits for club {club_id}")
    try:
        updated_splits = await fund_split_service.set_fund_splits_for_club(
            db=db, club_id=club_id, splits_in=fund_splits_in
        )
        log.info(f"Successfully set {len(updated_splits)} fund splits for club {club_id}")
        return updated_splits
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error setting fund splits for club {club_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while setting fund splits.")


# --- Member Transaction Endpoints ---

@router.post("/{club_id}/member-transactions/deposit", response_model=MemberTransactionRead, status_code=status.HTTP_201_CREATED, summary="Record Member Deposit", description="Records a cash deposit...", dependencies=[Depends(require_club_admin)])
async def record_member_deposit(club_id: uuid.UUID = Path(...), deposit_data: MemberTransactionCreateApi = Body(...), db: AsyncSession = Depends(get_db_session), current_user: User = Depends(get_current_active_user)):
    log.info(f"Received request to record deposit for user {deposit_data.user_id} in club {club_id} amount {deposit_data.amount} by admin {current_user.id}")
    deposit_in = MemberTransactionCreate(user_id=deposit_data.user_id, club_id=club_id, transaction_type=MemberTransactionType.DEPOSIT, amount=deposit_data.amount, transaction_date=deposit_data.transaction_date, notes=deposit_data.notes)
    try:
        new_member_tx = await accounting_service.process_member_deposit(db=db, deposit_in=deposit_in)
        log.info(f"Successfully recorded deposit {new_member_tx.id} for user {deposit_data.user_id} in club {club_id}")
        return new_member_tx
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error recording deposit for user {deposit_data.user_id} in club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while recording the deposit.")


@router.post("/{club_id}/member-transactions/withdrawal", response_model=MemberTransactionRead, status_code=status.HTTP_201_CREATED, summary="Record Member Withdrawal", description="Records a cash withdrawal...", dependencies=[Depends(require_club_admin)])
async def record_member_withdrawal(club_id: uuid.UUID = Path(...), withdrawal_data: MemberTransactionCreateApi = Body(...), db: AsyncSession = Depends(get_db_session), current_user: User = Depends(get_current_active_user)):
    log.info(f"Received request to record withdrawal for user {withdrawal_data.user_id} in club {club_id} amount {withdrawal_data.amount} by admin {current_user.id}")
    withdrawal_in = MemberTransactionCreate(user_id=withdrawal_data.user_id, club_id=club_id, transaction_type=MemberTransactionType.WITHDRAWAL, amount=withdrawal_data.amount, transaction_date=withdrawal_data.transaction_date, notes=withdrawal_data.notes)
    try:
        new_member_tx = await accounting_service.process_member_withdrawal(db=db, withdrawal_in=withdrawal_in)
        log.info(f"Successfully recorded withdrawal {new_member_tx.id} for user {withdrawal_data.user_id} in club {club_id}")
        return new_member_tx
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error recording withdrawal for user {withdrawal_data.user_id} in club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while recording the withdrawal.")


@router.get("/{club_id}/member-transactions", response_model=List[MemberTransactionRead], summary="List Member Transactions", description="Retrieves member deposits/withdrawals...", dependencies=[Depends(require_club_member)])
async def list_member_transactions(club_id: uuid.UUID = Path(...), user_id: uuid.UUID = Query(None), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=200), db: AsyncSession = Depends(get_db_session), requesting_membership: ClubMembership = Depends(require_club_member)):
    log.info(f"Request to list member transactions for club {club_id}, filter user_id: {user_id}, requested by user {requesting_membership.user_id}")
    membership_id_to_filter: uuid.UUID | None = None
    list_all_for_club = False
    is_admin = requesting_membership.role == ClubRole.ADMIN

    if user_id:
        is_self = requesting_membership.user_id == user_id
        if not is_self and not is_admin:
             log.warning(f"User {requesting_membership.user_id} (Role: {requesting_membership.role}) attempted to list transactions for different user {user_id} without admin rights.")
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not authorized to view transactions for this member.")
        if is_self:
             membership_id_to_filter = requesting_membership.id
        else:
             target_membership = await crud_membership.get_club_membership_by_user_and_club(db=db, user_id=user_id, club_id=club_id)
             if not target_membership: return []
             membership_id_to_filter = target_membership.id
    else:
        if not is_admin:
            log.warning(f"Non-admin user {requesting_membership.user_id} attempted to list all member transactions for club {club_id}.")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can list all member transactions for the club.")
        list_all_for_club = True
        log.info(f"Admin {requesting_membership.user_id} requesting all member transactions for club {club_id}")

    try:
        transactions = await crud_member_tx.get_multi_member_transactions(
            db=db,
            membership_id=membership_id_to_filter,
            club_id=club_id if list_all_for_club else None, # Pass club_id only if listing all
            skip=skip,
            limit=limit
        )
        log.info(f"Retrieved {len(transactions)} member transactions for club {club_id} (filter user: {user_id}, list_all: {list_all_for_club})")
        return transactions
    except Exception as e:
        log.exception(f"Unexpected error listing member transactions for club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while listing member transactions.")


@router.get("/{club_id}/member-transactions/{member_transaction_id}", response_model=MemberTransactionRead, summary="Get Member Transaction Details", description="Retrieves details for a specific member transaction...", dependencies=[Depends(require_club_member)])
async def get_single_member_transaction(club_id: uuid.UUID = Path(...), member_transaction_id: uuid.UUID = Path(...), db: AsyncSession = Depends(get_db_session), requesting_membership: ClubMembership = Depends(require_club_member)):
    log.info(f"Received request for member transaction {member_transaction_id} in club {club_id}")
    # Fetch transaction using CRUD (ensure it loads relationships needed by schema)
    transaction = await crud_member_tx.get_member_transaction(db=db, member_transaction_id=member_transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Member transaction {member_transaction_id} not found.")

    # Authorization: Check transaction belongs to the club and user has rights
    # Refresh needed if get_member_transaction doesn't load membership
    await db.refresh(transaction, attribute_names=['membership'])
    if not transaction.membership or transaction.membership.club_id != club_id:
         log.error(f"Mismatch: Member transaction {member_transaction_id} does not belong to club {club_id}.")
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Member transaction {member_transaction_id} not found in this club.")

    is_admin = requesting_membership.role == ClubRole.ADMIN
    is_self = requesting_membership.id == transaction.membership_id

    if not is_admin and not is_self:
        log.warning(f"User {requesting_membership.user_id} not authorized to view member transaction {member_transaction_id}.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this member transaction.")

    log.info(f"Successfully retrieved member transaction {member_transaction_id}")
    return transaction


@router.get("/{club_id}/members/{user_id}/statement", response_model=MemberStatementData, summary="Get Member Statement", description="Retrieves a statement for a specific member...", dependencies=[Depends(require_club_member)])
async def get_member_statement_endpoint(club_id: uuid.UUID = Path(...), user_id: uuid.UUID = Path(...), db: AsyncSession = Depends(get_db_session), requesting_membership: ClubMembership = Depends(require_club_member)):
    log.info(f"Received request for statement for user {user_id} in club {club_id} by user {requesting_membership.user_id}")
    is_self = requesting_membership.user_id == user_id
    is_admin = requesting_membership.role == ClubRole.ADMIN
    if not is_self and not is_admin:
        log.warning(f"User {requesting_membership.user_id} (Role: {requesting_membership.role}) is not authorized to view statement for user {user_id} in club {club_id}.")
        raise HTTPException( status_code=status.HTTP_403_FORBIDDEN, detail="User is not authorized to view this member statement." )
    log.debug(f"Authorization passed for user {requesting_membership.user_id} to view statement for user {user_id} in club {club_id} (Self: {is_self}, Admin: {is_admin}).")
    try:
        statement_data = await reporting_service.get_member_statement( db=db, club_id=club_id, user_id=user_id )
        log.info(f"Successfully generated statement for user {user_id} in club {club_id}")
        return statement_data
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error generating statement for user {user_id} in club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while generating the member statement.")


@router.post("/{club_id}/calculate-nav", response_model=UnitValueHistoryRead, status_code=status.HTTP_201_CREATED, summary="Calculate and Store NAV", description="Calculates the club's Net Asset Value (NAV)...", dependencies=[Depends(require_club_admin)])
async def trigger_nav_calculation(club_id: uuid.UUID = Path(...), calc_request: NavCalculationRequest = Body(...), db: AsyncSession = Depends(get_db_session), current_user: User = Depends(get_current_active_user)):
    log.info(f"Received request to calculate NAV for club {club_id} on {calc_request.valuation_date} by admin {current_user.id}")
    try:
        new_nav_history = await accounting_service.calculate_and_store_nav( db=db, club_id=club_id, valuation_date=calc_request.valuation_date )
        log.info(f"Successfully calculated and stored NAV for club {club_id} on {calc_request.valuation_date}")
        return new_nav_history
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error calculating NAV for club {club_id} on {calc_request.valuation_date}: {e}")
        raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while calculating NAV.", )

