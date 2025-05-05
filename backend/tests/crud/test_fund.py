# backend/tests/crud/test_fund.py

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError # If constraints exist (e.g., unique name per club)
from sqlalchemy.ext.asyncio import AsyncSession

# Import refactored CRUD function
from backend.crud import fund as crud_fund
from backend.models import Club, User, Fund
# Import only schemas needed for update
from backend.schemas import FundUpdate # Removed FundCreate

# Use refactored helpers
from .test_user import create_test_user
from .test_club import create_test_club_via_crud # Use refactored helper

pytestmark = pytest.mark.asyncio(loop_scope="function")

# Helper prepares data dict for refactored create_fund
async def create_test_fund_via_crud(
    db_session: AsyncSession, club: Club, name: str = "Test Strategy Fund", description: str = "A specific strategy fund"
) -> Fund:
    """Helper prepares data dict and calls refactored create_fund."""
    fund_data = {
        "club_id": club.id, # Pass club_id directly
        "name": name,
        "description": description,
        # Add other fields if needed by Fund model, e.g., brokerage_cash_balance
    }
    return await crud_fund.create_fund(db=db_session, fund_data=fund_data)


async def test_create_fund(db_session: AsyncSession):
    creator = await create_test_user(db_session, email="creator_f1@example.com", auth0_sub="auth0|f_creator1")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)
    fund_name = "Aggressive Growth Fund"
    fund_description = "High risk/reward"

    # Use the fund helper which calls the refactored CRUD
    created_fund = await create_test_fund_via_crud(
        db_session, club=club, name=fund_name, description=fund_description
    )

    assert created_fund is not None
    assert created_fund.club_id == club.id
    assert created_fund.name == fund_name
    assert created_fund.description == fund_description
    assert created_fund.id is not None
    # Assert default cash balance if applicable (assuming 0.00 from model)
    assert created_fund.brokerage_cash_balance == 0.00


async def test_get_fund(db_session: AsyncSession):
    creator = await create_test_user(db_session, email="creator_f2@example.com", auth0_sub="auth0|f_creator2")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Use the fund helper to create a fund to retrieve
    fund_name = "Fund To Get"
    created_fund = await create_test_fund_via_crud(db_session, club=club, name=fund_name)
    assert created_fund is not None # Ensure creation succeeded

    retrieved_fund = await crud_fund.get_fund(db=db_session, fund_id=created_fund.id)
    assert retrieved_fund is not None # This was the failing assertion
    assert retrieved_fund.id == created_fund.id
    assert retrieved_fund.name == fund_name


async def test_get_fund_not_found(db_session: AsyncSession):
    non_existent_id = uuid.uuid4()
    retrieved_fund = await crud_fund.get_fund(db=db_session, fund_id=non_existent_id)
    assert retrieved_fund is None


async def test_get_fund_by_club_and_name(db_session: AsyncSession):
    creator = await create_test_user(db_session, email="creator_f3@example.com", auth0_sub="auth0|f_creator3")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)
    fund_name = "Specific Fund"
    # Use the fund helper
    created_fund = await create_test_fund_via_crud(db_session, club=club, name=fund_name)

    retrieved_fund = await crud_fund.get_fund_by_club_and_name(
        db=db_session, club_id=club.id, name=fund_name
    )
    assert retrieved_fund is not None
    assert retrieved_fund.id == created_fund.id


async def test_get_multi_funds_by_club(db_session: AsyncSession):
    creator = await create_test_user(db_session, email="creator_f4@example.com", auth0_sub="auth0|f_creator4")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Use the fund helper
    fund1 = await create_test_fund_via_crud(db_session, club=club, name="Alpha Fund")
    fund2 = await create_test_fund_via_crud(db_session, club=club, name="Beta Fund")
    # Note: The 'Default Fund' is no longer automatically created by create_test_club_via_crud

    # Create another club and fund to ensure filtering works
    creator2 = await create_test_user(db_session, email="c2@c.com", auth0_sub="auth0|c2_fund")
    club2 = await create_test_club_via_crud(db_session, creator=creator2, name="Other Club")
    await create_test_fund_via_crud(db_session, club=club2, name="Gamma Fund")

    funds_for_club1 = await crud_fund.get_multi_funds(db=db_session, club_id=club.id, limit=10)

    # Should only have the two funds explicitly created for club1
    assert len(funds_for_club1) == 2
    # Order by name: Alpha, Beta
    expected_ids = {fund1.id, fund2.id}
    assert {f.id for f in funds_for_club1} == expected_ids
    # Check order if needed
    assert funds_for_club1[0].id == fund1.id # Alpha
    assert funds_for_club1[1].id == fund2.id # Beta


async def test_update_fund(db_session: AsyncSession):
    creator = await create_test_user(db_session, email="creator_f5@example.com", auth0_sub="auth0|f_creator5")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Use the fund helper
    fund_to_update = await create_test_fund_via_crud(db_session, club=club, name="Original Name")

    update_data = FundUpdate(description="Updated Description")
    updated_fund = await crud_fund.update_fund(
        db=db_session, db_obj=fund_to_update, obj_in=update_data
    )

    assert updated_fund is not None
    assert updated_fund.id == fund_to_update.id
    assert updated_fund.name == "Original Name" # Name not updated
    assert updated_fund.description == "Updated Description"

    refetched = await crud_fund.get_fund(db=db_session, fund_id=fund_to_update.id)
    assert refetched.description == "Updated Description"


async def test_delete_fund(db_session: AsyncSession):
    creator = await create_test_user(db_session, email="creator_f6@example.com", auth0_sub="auth0|f_creator6")
    # Use refactored club helper
    club = await create_test_club_via_crud(db_session, creator=creator)
    # Use the fund helper
    fund_to_delete = await create_test_fund_via_crud(db_session, club=club, name="To Be Deleted")
    fund_id = fund_to_delete.id

    # Ensure no dependencies exist that would block deletion (Positions, etc.)
    # If dependencies are created, deletion might raise IntegrityError unless cascades are set

    deleted_fund = await crud_fund.delete_fund(db=db_session, db_obj=fund_to_delete)
    assert deleted_fund.id == fund_id

    retrieved = await crud_fund.get_fund(db=db_session, fund_id=fund_id)
    assert retrieved is None

# Example constraint test if (club_id, name) must be unique
# async def test_create_duplicate_fund_name_in_club_fails(db_session: AsyncSession):
#     creator = await create_test_user(db_session, email="creator_f7@example.com", auth0_sub="auth0|f_creator7")
#     club = await create_test_club_via_crud(db_session, creator=creator)
#     fund_name = "Duplicate Fund Name"
#     await create_test_fund_via_crud(db_session, club=club, name=fund_name)
#
#     # Prepare data dict for refactored function
#     fund_data_dup = {
#         "club_id": club.id,
#         "name": fund_name,
#         "description": "Trying duplicate"
#     }
#     with pytest.raises(IntegrityError):
#          await crud_fund.create_fund(db=db_session, fund_data=fund_data_dup)
