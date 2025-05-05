# models/fund_split.py
from sqlalchemy import Column, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.core.database import Base
from .base_model import IdMixin, TimestampMixin, TableNameMixin

class FundSplit(IdMixin, TimestampMixin, TableNameMixin, Base):
    __tablename__ = 'fund_splits'

    club_id = Column(UUID(as_uuid=True), ForeignKey('clubs.id'), nullable=False, index=True)
    fund_id = Column(UUID(as_uuid=True), ForeignKey('funds.id'), nullable=False, index=True)
    
    # Percentage (e.g., 0.6 for 60%) - Ensure sum <= 1.0 per club in application logic
    split_percentage = Column(Numeric(5, 4), nullable=False) # Allows precision like 60.25% (0.6025)

    # Relationships
    club = relationship("Club", back_populates="fund_splits")
    # fund = relationship("Fund", back_populates="fund_split") # Relationship back to fund might not be strictly necessary

    # Constraints
    __table_args__ = (UniqueConstraint('club_id', 'fund_id', name='uq_club_fund_split'),)