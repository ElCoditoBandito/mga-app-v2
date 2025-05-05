# models/user.py
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
# Adjust imports as necessary
from backend.core.database import Base # Assuming Base is defined in database.py
from .base_model import IdMixin, TimestampMixin, TableNameMixin # Using BaseModel for id/timestamps

class User(IdMixin, TimestampMixin, TableNameMixin, Base):
    __tablename__ = 'users' # Explicit override if needed, else BaseModel handles it

    auth0_sub = Column(String, unique=True, index=True, nullable=False) # Auth0 User ID
    email = Column(String, unique=True, index=True, nullable=False) # Store email for convenience
    is_active = Column(Boolean, default=True)

    # Relationships
    memberships = relationship("ClubMembership", back_populates="user", cascade="all, delete-orphan")
    # --- REMOVED Outdated Relationship ---
    # Member transactions are now accessed via ClubMembership: user.memberships[i].member_transactions
    # member_transactions = relationship("MemberTransaction", back_populates="user")

    # Optional: Add a print statement for debugging imports if needed
    # print(f"--- Executing models/user.py --- Defining User class ---")
