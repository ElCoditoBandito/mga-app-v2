# backend/tests/crud/test_member_transaction.py

import uuid
from datetime import datetime, timezone, timedelta # Use datetime, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# Import refactored CRUD function
from backend.crud import member_transaction as crud_mem_tx
# Import models needed
from backend.models import Club, User, ClubMembership, MemberTransaction
from backend.models.enums import MemberTransactionType
# No longer need create schema
# from backend.schemas import MemberTransactionCreate

# Import refactored helpers
from .test_user import create_test_user
from .test_club import create_test_club_via_crud
from .test_club_membership import create_test_membership_via_crud # Use refactored helper

pytestmark = pytest.mark.asyncio(loop_scope="function")

# Helper prepares data dict for refactored create_member_transaction
async def create_test_member_transaction_via_crud(
    db_session: AsyncSession,
    membership: ClubMembership,
    tx_type: MemberTransactionType = MemberTransactionType.DEPOSIT,
    amount: Decimal = Decimal("1000.0"),
    tx_date: datetime | None = None, # Use datetime
    notes: str | None = None,
    # Unit fields are typically calculated later by service layer, omit from basic CRUD test
    # unit_value_used: Decimal | None = None,
    # units_transacted: Decimal | None = None,
) -> MemberTransaction:
    """Helper prepares data dict and calls refactored create_member_transaction."""
    if tx_date is None:
        tx_date = datetime.now(timezone.utc) # Use timezone-aware datetime

    member_tx_data = {
        "membership_id": membership.id,
        "transaction_type": tx_type,
        "amount": amount,
        "transaction_date": tx_date,
        "notes": notes,
        # "unit_value_used": unit_value_used, # Omit for basic CRUD test
        # "units_transacted": units_transacted, # Omit for basic CRUD test
    }
    # Filter out None values before passing to CRUD if model doesn't handle them
    # member_tx_data_filtered = {k: v for k, v in member_tx_data.items() if v is not None}
    # return await crud_mem_tx.create_member_transaction(db=db_session, member_tx_data=member_tx_data_filtered)
    # Or assume CRUD/model handles None
    return await crud_mem_tx.create_member_transaction(db=db_session, member_tx_data=member_tx_data)


# Helper to setup context with a membership using refactored helpers
async def setup_basic_mem_tx_context(db_session: AsyncSession):
    # Fix: Remove invalid 'username' argument
    user = await create_test_user(db_session, email=f"memtxuser_{uuid.uuid4()}@example.com", auth0_sub=f"auth0|memtx_{uuid.uuid4()}")
    creator = await create_test_user(db_session, email=f"memtxcreator_{uuid.uuid4()}@example.com", auth0_sub=f"auth0|memtx_cr_{uuid.uuid4()}")
    club = await create_test_club_via_crud(db_session, creator=creator)
    membership = await create_test_membership_via_crud(db_session, user=user, club=club)
    return membership


async def test_create_member_transaction_deposit(db_session: AsyncSession):
    membership = await setup_basic_mem_tx_context(db_session)
    tx_type = MemberTransactionType.DEPOSIT
    amount = Decimal("5000.00")
    tx_date = datetime(2024, 3, 10, 12, 0, 0, tzinfo=timezone.utc) # Use datetime
    notes_val = "Initial deposit"

    # Use the helper which calls the refactored CRUD
    created_tx = await create_test_member_transaction_via_crud(
        db_session,
        membership=membership,
        tx_type=tx_type,
        amount=amount,
        tx_date=tx_date,
        notes=notes_val
    )

    assert created_tx is not None
    assert created_tx.membership_id == membership.id
    assert created_tx.transaction_type == tx_type
    assert created_tx.amount == amount
    assert created_tx.transaction_date == tx_date
    assert created_tx.notes == notes_val
    assert created_tx.id is not None
    # Assert unit fields are None/default if not set by CRUD
    assert created_tx.unit_value_used is None
    assert created_tx.units_transacted is None


async def test_create_member_transaction_withdrawal(db_session: AsyncSession):
    membership = await setup_basic_mem_tx_context(db_session)
    tx_type = MemberTransactionType.WITHDRAWAL
    amount = Decimal("500.00")
    tx_date = datetime(2024, 4, 1, 9, 30, 0, tzinfo=timezone.utc) # Use datetime

    # Use helper which calls refactored CRUD
    created_tx = await create_test_member_transaction_via_crud(
        db_session, membership, tx_type=tx_type, amount=amount, tx_date=tx_date
    )

    assert created_tx is not None
    assert created_tx.transaction_type == tx_type
    assert created_tx.amount == amount


async def test_get_member_transaction(db_session: AsyncSession):
    membership = await setup_basic_mem_tx_context(db_session)
    # Use helper which calls refactored CRUD
    created_tx = await create_test_member_transaction_via_crud(db_session, membership)

    retrieved_tx = await crud_mem_tx.get_member_transaction(
        db=db_session, member_transaction_id=created_tx.id
    )

    assert retrieved_tx is not None
    assert retrieved_tx.id == created_tx.id
    assert retrieved_tx.membership_id == membership.id


async def test_get_member_transaction_not_found(db_session: AsyncSession):
    non_existent_id = uuid.uuid4()
    retrieved_tx = await crud_mem_tx.get_member_transaction(
        db=db_session, member_transaction_id=non_existent_id
    )
    assert retrieved_tx is None


async def test_get_multi_member_transactions_by_membership(db_session: AsyncSession):
    membership = await setup_basic_mem_tx_context(db_session)
    today = datetime.now(timezone.utc) # Use datetime
    tx1_date = today - timedelta(days=20)
    tx2_date = today - timedelta(days=10)
    tx3_date = today

    # Use helper which calls refactored CRUD
    tx1 = await create_test_member_transaction_via_crud(db_session, membership, tx_type=MemberTransactionType.DEPOSIT, tx_date=tx1_date, amount=1000)
    tx2 = await create_test_member_transaction_via_crud(db_session, membership, tx_type=MemberTransactionType.DEPOSIT, tx_date=tx2_date, amount=500)
    tx3 = await create_test_member_transaction_via_crud(db_session, membership, tx_type=MemberTransactionType.WITHDRAWAL, tx_date=tx3_date, amount=200)

    # Create another membership and transaction to test filtering
    # Fix: Remove invalid 'username' argument and provide unique auth0_sub
    user2 = await create_test_user(db_session, email=f"othermem_{uuid.uuid4()}@tx.com", auth0_sub=f"auth0|othermemtx_{uuid.uuid4()}")
    # Need creator/club for the second membership
    creator2 = await create_test_user(db_session, email=f"othercreator_{uuid.uuid4()}@tx.com", auth0_sub=f"auth0|othercrtx_{uuid.uuid4()}")
    club2 = await create_test_club_via_crud(db_session, creator=creator2, name=f"Other Club {uuid.uuid4()}")
    membership2 = await create_test_membership_via_crud(db_session, user=user2, club=club2)
    await create_test_member_transaction_via_crud(db_session, membership2, tx_date=today)

    transactions = await crud_mem_tx.get_multi_member_transactions(
        db=db_session, membership_id=membership.id, limit=10
    )

    assert len(transactions) == 3
    # Default order is desc date, desc created_at, desc id
    expected_ids_ordered = [tx3.id, tx2.id, tx1.id]
    actual_ids_ordered = [tx.id for tx in transactions]
    assert actual_ids_ordered == expected_ids_ordered


async def test_get_multi_member_transactions_pagination(db_session: AsyncSession):
    membership = await setup_basic_mem_tx_context(db_session)
    today = datetime.now(timezone.utc) # Use datetime
    # Use helper which calls refactored CRUD
    tx1 = await create_test_member_transaction_via_crud(db_session, membership, tx_date=today - timedelta(days=2))
    tx2 = await create_test_member_transaction_via_crud(db_session, membership, tx_date=today - timedelta(days=1))
    tx3 = await create_test_member_transaction_via_crud(db_session, membership, tx_date=today) # Assume created last

    # Get page 1 (limit 2, should be tx3, tx2)
    tx_page1 = await crud_mem_tx.get_multi_member_transactions(
        db=db_session, membership_id=membership.id, skip=0, limit=2
    )
    assert len(tx_page1) == 2
    assert tx_page1[0].id == tx3.id
    assert tx_page1[1].id == tx2.id

    # Get page 2 (limit 2, skip 2, should be tx1)
    tx_page2 = await crud_mem_tx.get_multi_member_transactions(
        db=db_session, membership_id=membership.id, skip=2, limit=2
    )
    assert len(tx_page2) == 1
    assert tx_page2[0].id == tx1.id

