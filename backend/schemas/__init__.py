# backend/schemas/__init__.py

"""
schemas Package Initialization

Re-exports key schemas for easier access from other parts of the application.
e.g., `from backend.schemas import UserRead` instead of
`from backend.schemas.user import UserRead`

**IMPORTANT:** Import order matters for resolving Pydantic forward references without
explicit model_rebuild() calls in individual files. Import base/referenced schemas first.
"""
import logging
from pydantic import ConfigDict

# Configure logging
log = logging.getLogger(__name__)

# Common Config for ORM models (Read schemas)
orm_config = ConfigDict(from_attributes=True)

# --- Stage 1: Import Base Schemas (often referenced by others) ---
from .asset import (
    AssetBase,
    AssetCreateOption,
    AssetCreateStock,
    AssetReadBasic,
    AssetRead,
    AssetUpdate,
)
from .user import (
    UserBase,
    UserCreate,
    UserRead,
    UserReadBasic,
    UserUpdate,
)
from .club import (
    ClubBase,
    ClubCreate,
    ClubRead,
    ClubReadBasic,
    ClubUpdate,
    ClubMembershipBase,
    ClubMembershipCreate,
    ClubMembershipRead,
    ClubMembershipReadBasicUser,
    ClubMembershipUpdate,
    ClubPortfolio,
)

from .fund import (
    FundBase,
    FundCreate,
    FundRead,
    FundReadBasic,
    FundUpdate,
    FundReadWithPositions,
    FundReadDetailed,
    FundPerformanceHistoryResponse,
    FundSplitBase,
    FundSplitCreate,
    FundSplitRead,
    FundSplitUpdate,
    FundSplitItem,
    FundPerformanceHistoryPoint,
)

from .member_transaction import (
    MemberTransactionBase,
    MemberTransactionCreate,
    MemberTransactionRead,
    MemberTransactionReadBasic,
)   

from .position import (
    PositionBase,
    PositionRead,
    
)
from .reporting import (
    MemberStatementData,
    ClubPerformanceData,
)
from .transaction import (
    TransactionBase,
    TransactionCreateBase,
    TransactionCreateTrade,
    TransactionCreateDividendBrokerageInterest,
    TransactionCreateBankInterest,
    TransactionCreateClubExpense,
    TransactionCreateCashTransfer,
    TransactionCreateOptionLifecycle,
    TransactionCreateAdjustmentReversal,
    TransactionUpdate,
    TransactionReadBasic,
    TransactionRead,

)
from .unit_value import (
    UnitValueHistoryBase,
    UnitValueHistoryRead,
)

from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserRead,
    UserReadBasic,
    
)

PositionRead.model_rebuild() # Add rebuild for PositionRead
MemberTransactionRead.model_rebuild() # Add rebuild for MemberTransactionRead
UnitValueHistoryRead.model_rebuild() # Add rebuild for UnitValueHistoryRead
ClubPortfolio.model_rebuild()
MemberStatementData.model_rebuild()
ClubRead.model_rebuild()
ClubReadBasic.model_rebuild()
ClubMembershipReadBasicUser.model_rebuild()
ClubMembershipRead.model_rebuild()
FundReadDetailed.model_rebuild()
FundReadWithPositions.model_rebuild()
FundRead.model_rebuild()
UserReadBasic.model_rebuild()
ClubMembershipRead.model_rebuild()
TransactionRead.model_rebuild()
