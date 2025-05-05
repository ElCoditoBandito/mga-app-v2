"""
Pydantic Schemas for User Resource
"""
import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING # Keep List if future nesting is planned

from pydantic import BaseModel, Field

# Import shared ORM config
from . import orm_config

# Import schemas needed for potential future nesting

#if TYPE_CHECKING:
    # from .club import ClubMembershipRead # Example if nesting memberships

class UserBase(BaseModel):
    email: str = Field(..., example="member@example.com")
    is_active: bool = True

# Schema for creating a user (usually from Auth0 info)
class UserCreate(UserBase):
    auth0_sub: str = Field(..., example="auth0|unique-user-identifier")

# Schema for updating a user (subset of fields)
class UserUpdate(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None
    # model_config = ConfigDict(extra='forbid') # Optional: Forbid extra fields on update

# Basic Read schema (for nesting in other resources)
class UserReadBasic(UserBase):
    id: uuid.UUID
    model_config = orm_config

# Full Read schema (potentially including sensitive info like auth0_sub)
class UserRead(UserBase):
    id: uuid.UUID
    auth0_sub: str # Included for reference, maybe only for admins/self
    created_at: datetime
    updated_at: datetime
    # Avoid nesting memberships/transactions by default to prevent large payloads
    # memberships: List['ClubMembershipRead'] = [] # Requires forward refs or separate definition order
    # member_transactions: List['MemberTransactionRead'] = []
    model_config = orm_config