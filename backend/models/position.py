# models/position.py
from sqlalchemy import Column, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.core.database import Base
from .base_model import IdMixin, TimestampMixin, TableNameMixin

class Position(IdMixin, TimestampMixin, TableNameMixin, Base):
    __tablename__ = 'positions'

    fund_id = Column(UUID(as_uuid=True), ForeignKey('funds.id'), nullable=False)
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id'), nullable=False)

    quantity = Column(Numeric(18, 6), nullable=False) # Shares or Contracts, allow decimals for potential splits/etc.
    # Average cost basis per share/contract - calculated and updated by transactions
    average_cost_basis = Column(Numeric(15, 4), nullable=False, default=0.00)

    # Relationships
    fund = relationship("Fund", back_populates="positions")
    asset = relationship("Asset", back_populates="positions")

    # Constraints - A fund should only have one position record per asset
    __table_args__ = (UniqueConstraint('fund_id', 'asset_id', name='uq_fund_asset_position'),)