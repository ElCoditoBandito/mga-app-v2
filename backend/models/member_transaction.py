# models/member_transaction.py
from sqlalchemy import Column, Enum as SQLEnum, Numeric, DateTime, ForeignKey, Text # Added Text for notes
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
# Adjust imports as necessary
from backend.core.database import Base
from .base_model import IdMixin, TimestampMixin, TableNameMixin
from .enums import MemberTransactionType

class MemberTransaction(IdMixin, TimestampMixin, TableNameMixin, Base):
    __tablename__ = 'member_transactions' # Records Deposits and Withdrawals

    # Removed user_id and club_id - these should link via ClubMembership
    # user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    # club_id = Column(UUID(as_uuid=True), ForeignKey('clubs.id'), nullable=False)
    membership_id = Column(UUID(as_uuid=True), ForeignKey('club_memberships.id'), nullable=False, index=True)

    transaction_type = Column(SQLEnum(MemberTransactionType, name="member_transaction_type_enum", create_type=True, native_enum=True), nullable=False) # Added native_enum=True
    # --- CHANGE HERE: Make DateTime timezone-aware ---
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True) # When deposit/withdrawal occurred
    amount = Column(Numeric(15, 2), nullable=False) # Cash amount deposited or withdrawn

    # Unit value used for this transaction (from UnitValueHistory on transaction_date)
    unit_value_used = Column(Numeric(20, 8), nullable=True) # Made nullable - might not be set immediately
    # Number of units issued (deposit) or redeemed (withdrawal)
    units_transacted = Column(Numeric(25, 8), nullable=True) # Made nullable - might not be set immediately

    # Optional notes field
    notes = Column(Text, nullable=True)

    # Relationships
    # user = relationship("User", back_populates="member_transactions") # Link via membership
    # club = relationship("Club", back_populates="member_transactions") # Link via membership
    membership = relationship("ClubMembership", back_populates="member_transactions")

