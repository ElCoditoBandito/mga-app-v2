# backend/api/v1/endpoints/transactions.py

import uuid
import logging
from typing import List, Any, Sequence, Union

try:
    from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body
    from sqlalchemy.ext.asyncio import AsyncSession
    from pydantic import BaseModel
except ImportError:
    # Dummy imports...
    class APIRouter:
        def post(self, *args, **kwargs): pass
        def get(self, *args, **kwargs): pass
    def Depends(dependency: Any | None = None) -> Any: return None
    class HTTPException(Exception): pass
    class Status: HTTP_201_CREATED = 201; HTTP_500_INTERNAL_SERVER_ERROR = 500; HTTP_404_NOT_FOUND = 404; HTTP_403_FORBIDDEN = 403; HTTP_400_BAD_REQUEST = 400; HTTP_409_CONFLICT = 409; HTTP_200_OK = 200; HTTP_422_UNPROCESSABLE_ENTITY = 422
    status = Status()
    def Path(*args, **kwargs): return uuid.uuid4()
    def Query(*args, **kwargs): return None
    def Body(*args, **kwargs): return None
    class AsyncSession: pass
    class BaseModel: pass

# Import dependencies, schemas, services, models
try:
    from backend.api.dependencies import (
        get_db_session, get_current_active_user,
        require_club_admin, require_club_member
    )
    from backend.schemas import (
        TransactionRead, TransactionCreateTrade,
        TransactionCreateDividendBrokerageInterest,
        TransactionCreateCashTransfer, TransactionCreateOptionLifecycle,
        TransactionReadBasic # Added Basic Read
    )
    from backend.services import transaction_service
    from backend.models import User, ClubMembership, Fund, Transaction
    from backend.crud import fund as crud_fund, transaction as crud_transaction # Added transaction crud
except ImportError as e:
    print(f"WARNING: Failed to import dependencies/schemas/services: {e}. Transaction endpoints may not work.")
    # Dummy definitions...
    async def get_db_session() -> AsyncSession: return AsyncSession()
    async def get_current_active_user() -> User: return User(id=uuid.uuid4(), is_active=True, auth0_sub="dummy|sub")
    async def require_club_admin(*args, **kwargs) -> ClubMembership: return ClubMembership(id=uuid.uuid4())
    async def require_club_member(*args, **kwargs) -> ClubMembership: return ClubMembership(id=uuid.uuid4())
    class TransactionRead: pass
    class TransactionCreateTrade: fund_id: uuid.UUID | None = None
    class TransactionCreateDividendBrokerageInterest: fund_id: uuid.UUID | None = None; transaction_type: Any
    class TransactionCreateCashTransfer: transaction_type: Any
    class TransactionCreateOptionLifecycle: fund_id: uuid.UUID | None = None; transaction_type: Any; asset_id: uuid.UUID
    class TransactionReadBasic: pass
    class User: id: uuid.UUID; is_active: bool; auth0_sub: str = "dummy|sub"
    class ClubMembership: id: uuid.UUID
    class Fund: club_id: uuid.UUID
    class Transaction: id: uuid.UUID; fund: Fund | None = None # Add relationship for check
    class transaction_service:
        @staticmethod
        async def process_trade_transaction(db: AsyncSession, *, trade_in: TransactionCreateTrade) -> Any: return {"id": uuid.uuid4()}
        @staticmethod
        async def process_cash_receipt_transaction(db: AsyncSession, *, cash_receipt_in: TransactionCreateDividendBrokerageInterest) -> Any: return {"id": uuid.uuid4()}
        @staticmethod
        async def process_cash_transfer_transaction(db: AsyncSession, *, transfer_in: TransactionCreateCashTransfer, club_id: uuid.UUID) -> Union[Transaction, Sequence[Transaction], None]: return Transaction(id=uuid.uuid4())
        @staticmethod
        async def process_option_lifecycle_transaction(db: AsyncSession, *, lifecycle_in: TransactionCreateOptionLifecycle) -> Transaction: return Transaction(id=uuid.uuid4())
        @staticmethod
        async def list_transactions(db: AsyncSession, *, club_id: uuid.UUID, fund_id: uuid.UUID | None = None, asset_id: uuid.UUID | None = None, skip: int = 0, limit: int = 100) -> Sequence[Transaction]: return [Transaction(id=uuid.uuid4())]
        # Add dummy get_transaction_by_id if needed by endpoints
        @staticmethod
        async def get_transaction_by_id(db: AsyncSession, transaction_id: uuid.UUID) -> Transaction: return Transaction(id=transaction_id)
    class crud_fund:
        @staticmethod
        async def get_fund(db: AsyncSession, fund_id: uuid.UUID) -> Fund | None: return Fund(club_id=uuid.uuid4())
    class crud_transaction:
        @staticmethod
        async def get_transaction(db: AsyncSession, transaction_id: uuid.UUID) -> Transaction | None:
             # Simulate finding a transaction belonging to a dummy club
             return Transaction(id=transaction_id, fund=Fund(club_id=uuid.uuid4()))


# Configure logging
log = logging.getLogger(__name__)

# Create router instance
# Prefix "/clubs/{club_id}/transactions" applied in api/v1/__init__.py
router = APIRouter()


# --- Fund Transaction Endpoints ---

@router.post("/trade", response_model=TransactionRead, status_code=status.HTTP_201_CREATED, summary="Record Investment Trade", description="Records a stock or option trade...", dependencies=[Depends(require_club_admin)])
async def record_trade(club_id: uuid.UUID = Path(...), trade_data: TransactionCreateTrade = Body(...), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request to record trade in club {club_id}, fund {trade_data.fund_id}")
    if not trade_data.fund_id: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="fund_id is required in the request body for trade transactions.")
    fund = await crud_fund.get_fund(db=db, fund_id=trade_data.fund_id)
    if not fund or fund.club_id != club_id: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Fund {trade_data.fund_id} does not belong to club {club_id}.")
    try:
        new_transaction = await transaction_service.process_trade_transaction(db=db, trade_in=trade_data)
        log.info(f"Successfully recorded trade transaction {new_transaction.id} in fund {trade_data.fund_id}")
        return new_transaction
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error recording trade for fund {trade_data.fund_id} in club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while recording the trade.")


@router.post("/cash-receipt", response_model=TransactionRead, status_code=status.HTTP_201_CREATED, summary="Record Cash Receipt (Dividend/Interest)", description="Records a dividend or brokerage interest payment...", dependencies=[Depends(require_club_admin)])
async def record_cash_receipt(club_id: uuid.UUID = Path(...), receipt_data: TransactionCreateDividendBrokerageInterest = Body(...), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request to record cash receipt in club {club_id}, fund {receipt_data.fund_id}, type {receipt_data.transaction_type}")
    if not receipt_data.fund_id: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="fund_id is required in the request body for cash receipt transactions.")
    fund = await crud_fund.get_fund(db=db, fund_id=receipt_data.fund_id)
    if not fund or fund.club_id != club_id: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Fund {receipt_data.fund_id} does not belong to club {club_id}.")
    try:
        new_transaction = await transaction_service.process_cash_receipt_transaction(db=db, cash_receipt_in=receipt_data)
        log.info(f"Successfully recorded cash receipt transaction {new_transaction.id} in fund {receipt_data.fund_id}")
        return new_transaction
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error recording cash receipt for fund {receipt_data.fund_id} in club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while recording the cash receipt.")


@router.post("/cash-transfer", response_model=Union[TransactionRead, List[TransactionRead]], status_code=status.HTTP_201_CREATED, summary="Record Cash Transfer", description="Records a cash transfer...", dependencies=[Depends(require_club_admin)])
async def record_cash_transfer(club_id: uuid.UUID = Path(...), transfer_data: TransactionCreateCashTransfer = Body(...), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request to record cash transfer type {transfer_data.transaction_type} for club {club_id}")
    try:
        result = await transaction_service.process_cash_transfer_transaction(db=db, transfer_in=transfer_data, club_id=club_id)
        if isinstance(result, list): log.info(f"Successfully recorded BANK_TO_BROKERAGE transfer (split into {len(result)} transactions) for club {club_id}")
        elif result: log.info(f"Successfully recorded cash transfer transaction {result.id} for club {club_id}")
        else: log.warning(f"Cash transfer processing for club {club_id} completed but returned no transaction object."); return []
        return result
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error recording cash transfer for club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while recording the cash transfer.")


@router.post("/option-lifecycle", response_model=TransactionRead, status_code=status.HTTP_201_CREATED, summary="Record Option Lifecycle Event", description="Records an option expiration, exercise, or assignment...", dependencies=[Depends(require_club_admin)])
async def record_option_lifecycle(club_id: uuid.UUID = Path(...), lifecycle_data: TransactionCreateOptionLifecycle = Body(...), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request to record option lifecycle event type {lifecycle_data.transaction_type} for option {lifecycle_data.asset_id} in club {club_id}, fund {lifecycle_data.fund_id}")
    if not lifecycle_data.fund_id: raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="fund_id is required in the request body for option lifecycle transactions.")
    fund = await crud_fund.get_fund(db=db, fund_id=lifecycle_data.fund_id)
    if not fund or fund.club_id != club_id: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Fund {lifecycle_data.fund_id} does not belong to club {club_id}.")
    try:
        new_transaction = await transaction_service.process_option_lifecycle_transaction(db=db, lifecycle_in=lifecycle_data)
        log.info(f"Successfully recorded option lifecycle transaction {new_transaction.id} in fund {lifecycle_data.fund_id}")
        return new_transaction
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error recording option lifecycle event for fund {lifecycle_data.fund_id} in club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while recording the option lifecycle event.")


@router.get("", response_model=List[TransactionRead], summary="List Fund Transactions", description="Retrieves a list of fund-level transactions...", dependencies=[Depends(require_club_member)])
async def list_fund_transactions(club_id: uuid.UUID = Path(...), fund_id: uuid.UUID = Query(None), asset_id: uuid.UUID = Query(None), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: AsyncSession = Depends(get_db_session)):
    log.info(f"Received request to list transactions for club {club_id} with filters - fund_id: {fund_id}, asset_id: {asset_id}")
    if fund_id:
        fund = await crud_fund.get_fund(db=db, fund_id=fund_id)
        if not fund or fund.club_id != club_id:
            log.warning(f"Attempt to list transactions for fund {fund_id} which does not belong to club {club_id}.")
            raise HTTPException( status_code=status.HTTP_403_FORBIDDEN, detail=f"Fund {fund_id} does not belong to club {club_id}." )
    try:
        transactions = await transaction_service.list_transactions( db=db, club_id=club_id, fund_id=fund_id, asset_id=asset_id, skip=skip, limit=limit )
        log.info(f"Retrieved {len(transactions)} transactions for club {club_id} (filters applied)")
        return transactions
    except HTTPException as e: raise e
    except Exception as e:
        log.exception(f"Unexpected error listing transactions for club {club_id}: {e}")
        raise HTTPException( status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while listing transactions.", )


@router.get("/{transaction_id}", response_model=TransactionRead, summary="Get Transaction Details", description="Retrieves details for a specific fund-level transaction. Requires membership.", dependencies=[Depends(require_club_member)])
async def get_single_transaction(club_id: uuid.UUID = Path(...), transaction_id: uuid.UUID = Path(...), db: AsyncSession = Depends(get_db_session)):
    """ API endpoint to get details for a specific fund transaction. """
    log.info(f"Received request for transaction {transaction_id} in club {club_id}")
    # Fetch the transaction using CRUD (ensure it loads relationships needed by schema)
    transaction = await crud_transaction.get_transaction(db=db, transaction_id=transaction_id)
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transaction {transaction_id} not found.")

    # Authorization Check: Ensure the transaction belongs to the correct club
    # The get_transaction CRUD now loads the fund relationship
    if not transaction.fund or transaction.fund.club_id != club_id:
        log.error(f"Mismatch: Transaction {transaction_id} does not belong to club {club_id}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Transaction {transaction_id} not found in this club.")

    log.info(f"Successfully retrieved transaction {transaction_id}")
    return transaction

