# backend/schemas/__init__.py

"""
schemas Package Initialization

Re-exports key schemas for easier access from other parts of the application.
e.g., `from backend.schemas import UserRead` instead of
`from backend.schemas.user import UserRead`

**IMPORTANT:** Import order matters for resolving Pydantic forward references without
explicit model_rebuild() calls in individual files. Import base/referenced schemas first.
"""
from pydantic import ConfigDict

# Common Config for ORM models (Read schemas)
orm_config = ConfigDict(from_attributes=True)

# --- Stage 1: Import Base Schemas (often referenced by others) ---
from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserRead,
    UserReadBasic, # Referenced by ClubMembershipRead, MemberTransactionRead
)
from .asset import (
    AssetBase,
    AssetCreateStock,
    AssetCreateOption,
    AssetUpdate,
    AssetRead,
    AssetReadBasic, # Referenced by PositionRead, TransactionRead
)
from .club import (
    ClubBase,
    ClubCreate,
    ClubUpdate,
    # ClubRead, # Define later - references others
    ClubReadBasic, # Referenced by ClubMembershipRead, MemberTransactionRead, UnitValueHistoryRead, FundRead
    ClubMembershipBase,
    ClubMembershipCreate,
    ClubMembershipUpdate,
    # ClubMembershipRead, # Define later - references UserReadBasic, ClubReadBasic
    # ClubMembershipReadBasicUser, # Define later - references UserReadBasic
    # ClubPortfolio, # Define later - references PositionRead, UnitValueHistoryRead
)
from .fund import (
    FundBase,
    FundCreate,
    FundUpdate,
    # FundRead, # Define later - references ClubReadBasic
    FundReadBasic, # Referenced by PositionRead, TransactionRead, FundSplitRead, FundReadWithPositions
    # FundReadWithPositions, # Define later - references PositionRead
    FundSplitBase,
    FundSplitCreate,
    FundSplitUpdate,
    # FundSplitRead, # Define later - references FundReadBasic
    FundSplitItem, # Used for API input, no forward refs
)

# --- Stage 2: Import Schemas that Depend on Stage 1 ---
from .position import (
    PositionBase,
    PositionRead, # Depends on AssetReadBasic, FundReadBasic
)
from .unit_value import (
    UnitValueHistoryBase,
    UnitValueHistoryRead, # Depends on ClubReadBasic
)
from .fund import ( # Re-import to define schemas dependent on Stage 1
    FundRead, # Depends on ClubReadBasic
    FundSplitRead, # Depends on FundReadBasic
    FundReadWithPositions, # Depends on PositionRead (defined above)
)
from .club import ( # Re-import to define schemas dependent on Stage 1
     ClubMembershipRead, # Depends on UserReadBasic, ClubReadBasic
     ClubMembershipReadBasicUser, # Depends on UserReadBasic
)
from .member_transaction import (
    MemberTransactionBase,
    MemberTransactionCreate, # Note: Service uses this, API uses CreateApi variation
    MemberTransactionRead, # Depends on UserReadBasic, ClubReadBasic
)
from .transaction import (
    TransactionBase,
    TransactionUpdate,
    # TransactionRead, # Define later - depends on AssetReadBasic, FundReadBasic
    TransactionReadBasic, # No forward refs here
    TransactionCreateBase,
    TransactionCreateTrade,
    TransactionCreateDividendBrokerageInterest,
    TransactionCreateBankInterest,
    TransactionCreateClubExpense,
    TransactionCreateCashTransfer,
    TransactionCreateOptionLifecycle,
    TransactionCreateAdjustmentReversal,
)
# --- NEW: Import Reporting Schemas ---
from .reporting import (
    MemberStatementData, # Depends on MemberTransactionRead (defined above)
    ClubPerformanceData, # No forward refs here
)
# --- END NEW ---

# --- Stage 3: Import Schemas that Depend on Stage 1 & 2 ---
from .transaction import ( # Re-import to define TransactionRead
    TransactionRead, # Depends on AssetReadBasic, FundReadBasic
)
from .club import ( # Re-import to define schemas dependent on Stage 1 & 2
    ClubRead, # Depends on ClubMembershipReadBasicUser, FundReadBasic, FundSplitRead
    ClubPortfolio, # Depends on PositionRead, UnitValueHistoryRead
)


# --- (Optional) Centralized Rebuild ---
# Keep commented out unless import order proves insufficient
# try:
#     # ... (list all schemas needing rebuild) ...
#     MemberStatementData.model_rebuild(force=True) # Add new ones if needed
#     # ...
#     print("--- Schemas: Forward references rebuild executed centrally ---")
# except NameError as e:
#     print(f"!!! FAILED to rebuild schema forward refs in schemas/__init__.py: {e}")
#     raise e
# except Exception as e:
#     print(f"!!! UNEXPECTED error during schema forward ref rebuild: {e}")
#     raise e

