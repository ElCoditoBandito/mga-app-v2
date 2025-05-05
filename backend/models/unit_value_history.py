# models/unit_value_history.py
from sqlalchemy import Column, Numeric, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.core.database import Base
from .base_model import IdMixin, TimestampMixin, TableNameMixin

class UnitValueHistory(IdMixin, TimestampMixin, TableNameMixin, Base):
    __tablename__ = 'unit_value_histories'

    club_id = Column(UUID(as_uuid=True), ForeignKey('clubs.id'), nullable=False)
    valuation_date = Column(Date, nullable=False, index=True)

    total_club_value = Column(Numeric(20, 2), nullable=False) # Market value positions + all cash (brokerage + bank)
    total_units_outstanding = Column(Numeric(25, 8), nullable=False) # High precision for units
    unit_value = Column(Numeric(20, 8), nullable=False) # High precision for NAV per unit

    # Relationships
    club = relationship("Club", back_populates="unit_value_history")

    # Constraints - One record per club per day
    __table_args__ = (UniqueConstraint('club_id', 'valuation_date', name='uq_club_valuation_date'),)