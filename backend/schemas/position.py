# backend/schemas/position.py

"""
Pydantic Schemas for Position Resource
"""
import uuid
import logging # Import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from pydantic import BaseModel, Field

# Import shared ORM config and other necessary schemas
from . import orm_config

log = logging.getLogger(__name__) # Logger for rebuild messages

if TYPE_CHECKING:
    # Use real imports for type checking
    from .asset import AssetReadBasic
    from .fund import FundReadBasic


class PositionBase(BaseModel):
    fund_id: uuid.UUID
    asset_id: uuid.UUID
    quantity: Decimal = Field(..., max_digits=18, decimal_places=6, example=Decimal("100.00"))
    average_cost_basis: Decimal = Field(..., max_digits=15, decimal_places=4, example=Decimal("150.2550"))

# Positions are usually modified via Transactions, so no Create/Update schemas needed for typical API flow

class PositionRead(PositionBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    asset: 'AssetReadBasic' # Nest basic asset details
    fund: 'FundReadBasic' # Nest basic fund details
    model_config = orm_config

# --- Resolve Forward References ---
# Explicitly rebuild models defined in *this file* that use forward references.
log.debug("Attempting model rebuild in schemas/position.py...")
try:
    PositionRead.model_rebuild(force=True)
    log.debug("Model rebuild successful in schemas/position.py.")
except NameError as e:
     log.error(f"FAILED model rebuild in schemas/position.py (NameError): {e}. Check import order in __init__.py or dependencies.")
     # Don't raise here, let centralized rebuild try later if needed
except Exception as e:
     log.error(f"FAILED model rebuild in schemas/position.py (Other Error): {e}", exc_info=True)
     # Don't raise here

