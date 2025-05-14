# models/club_membership.py
from sqlalchemy import Column, Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

# Adjust imports as necessary
from backend.core.database import Base
from .base_model import IdMixin, TimestampMixin, TableNameMixin
from .enums import ClubRole

class ClubMembership(IdMixin, TimestampMixin, TableNameMixin, Base):
    __tablename__ = 'club_memberships'

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True) # Added index
    club_id = Column(UUID(as_uuid=True), ForeignKey('clubs.id'), nullable=False, index=True) # Added index
    role = Column(SQLEnum(ClubRole, name="club_role_enum", create_type=True, native_enum=True), nullable=False, default=ClubRole.Member) # Keep enum fixes

    # Relationships
    user = relationship("User", back_populates="memberships")
    club = relationship("Club", back_populates="memberships")

    # --- ADDED Relationship to MemberTransaction ---
    # This defines the "one-to-many" side from ClubMembership to MemberTransaction
    member_transactions = relationship(
        "MemberTransaction",
        back_populates="membership",
        cascade="all, delete-orphan", # If a membership is deleted, delete its transactions
        lazy="select" # Or "dynamic" if you expect many transactions per member
    )

    # Constraints
    __table_args__ = (UniqueConstraint('user_id', 'club_id', name='uq_user_club'),)

