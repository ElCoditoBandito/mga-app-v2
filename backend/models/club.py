# models/club.py
from sqlalchemy import Column, String, Numeric, ForeignKey # Add ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID # Import UUID

# Adjust imports as necessary for your project structure
from backend.core.database import Base
from .base_model import IdMixin, TimestampMixin, TableNameMixin

class Club(IdMixin, TimestampMixin, TableNameMixin, Base):
    __tablename__ = 'clubs'

    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    # Club Level Cash Account
    bank_account_balance = Column(Numeric(15, 2), nullable=False, default=0.00) # Precision for currency

    creator_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)

    # Relationships
    creator = relationship("User") # Simple relationship to the User who created the club

    memberships = relationship("ClubMembership", back_populates="club", cascade="all, delete-orphan")
    funds = relationship("Fund", back_populates="club", cascade="all, delete-orphan")
    unit_value_history = relationship("UnitValueHistory", back_populates="club", cascade="all, delete-orphan")
    # --- REMOVED Outdated Relationship ---
    # Member transactions are now accessed via ClubMembership: club.memberships[i].member_transactions
    # member_transactions = relationship("MemberTransaction", back_populates="club")
    fund_splits = relationship("FundSplit", back_populates="club", cascade="all, delete-orphan") # Configuration for splits

