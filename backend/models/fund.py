# models/fund.py
from sqlalchemy import Column, String, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.core.database import Base
from .base_model import IdMixin, TimestampMixin, TableNameMixin

class Fund(IdMixin, TimestampMixin, TableNameMixin, Base):
    __tablename__ = 'funds'

    club_id = Column(UUID(as_uuid=True), ForeignKey('clubs.id'), nullable=False)
    name = Column(String, nullable=False, default="General Fund")
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False) # Allow deactivating funds

    # Fund Level Cash Account
    brokerage_cash_balance = Column(Numeric(15, 2), nullable=False, default=0.00)

    # Relationships
    club = relationship("Club", back_populates="funds")
    positions = relationship("Position", back_populates="fund", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="fund", cascade="all, delete-orphan") # All transactions related to this fund
    fund_split = relationship("FundSplit", back_populates="fund", uselist=False) # A fund can have one split setting