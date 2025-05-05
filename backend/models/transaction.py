# models/transaction.py
from sqlalchemy import Column, Enum as SQLEnum, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, foreign, remote # Import foreign and remote
from sqlalchemy.dialects.postgresql import UUID
# Adjust imports as necessary
from backend.core.database import Base
from .base_model import IdMixin, TimestampMixin, TableNameMixin
from .enums import TransactionType

class Transaction(IdMixin, TimestampMixin, TableNameMixin, Base):
    __tablename__ = 'transactions'

    fund_id = Column(UUID(as_uuid=True), ForeignKey('funds.id'), nullable=True) # Can be null for club-level tx
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id'), nullable=True) # Null for cash-only tx

    transaction_type = Column(SQLEnum(TransactionType, name="transaction_type_enum", create_type=True, native_enum=True), nullable=False, index=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False, index=True) # Effective date/time of the transaction

    # Common transaction fields (nullable depending on type)
    quantity = Column(Numeric(18, 6), nullable=True) # Shares or Contracts
    price_per_unit = Column(Numeric(15, 4), nullable=True) # Price per share or premium per contract
    total_amount = Column(Numeric(15, 2), nullable=True) # Gross amount (e.g., Quantity * Price), or deposit/expense amount
    fees_commissions = Column(Numeric(10, 2), nullable=True, default=0.00)

    # Description / Notes
    description = Column(Text, nullable=True)

    # Link for complex events (e.g., Option Exercise links option close tx with stock buy tx)
    related_transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.id'), nullable=True)

    # Fields for Corrections/Reversals
    reverses_transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.id'), nullable=True, index=True) # Link to the transaction being reversed

    # Relationships
    fund = relationship("Fund", back_populates="transactions")
    asset = relationship("Asset", back_populates="transactions")

    # --- FIXED Self-Referential Relationships using primaryjoin ---
    related_transaction_link = relationship(
        "Transaction",
        # Define the join condition explicitly:
        # Join where the remote Transaction's id (marked with remote())
        # matches the current Transaction's related_transaction_id (marked with foreign())
        primaryjoin=lambda: remote(Transaction.id) == foreign(Transaction.related_transaction_id),
        uselist=False,
        lazy="select",
        viewonly=True # Often useful for self-refs if not modifying through this link
    )

    reverses_transaction_link = relationship(
        "Transaction",
        # Define the join condition explicitly:
        # Join where the remote Transaction's id (marked with remote())
        # matches the current Transaction's reverses_transaction_id (marked with foreign())
        primaryjoin=lambda: remote(Transaction.id) == foreign(Transaction.reverses_transaction_id),
        uselist=False,
        lazy="select",
        viewonly=True # Often useful for self-refs if not modifying through this link
    )
    # --- END FIX ---

    # Optional: Define the other side of the self-referential relationships if needed
    # (e.g., a list of transactions that relate to or reverse this one)
    # related_to_transactions = relationship("Transaction", primaryjoin=lambda: Transaction.id == foreign(Transaction.related_transaction_id), viewonly=True)
    # reversed_by_transactions = relationship("Transaction", primaryjoin=lambda: Transaction.id == foreign(Transaction.reverses_transaction_id), viewonly=True)


