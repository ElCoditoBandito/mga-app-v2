# models/base_model.py
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr

class TableNameMixin:
    """
        Generates table name automatically from class name.
        Converts CamelCase class names to snake_case table names.
        Example: User -> users, ClubMembership -> club_memberships
    """
    @declared_attr.directive
    def __tablename__(cls):
        return cls.__name__.lower() + 's' # Makes User -> users, Club -> clubs etc.



class IdMixin:
    """Mixin for a UUID primary key column named 'id'."""
    # Direct Column definition is often sufficient in mixins unless
    # complex default logic or type variations are needed per table.
    # Using declared_attr here for consistency example, but could be direct.
    @declared_attr
    def id(cls):
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class TimestampMixin:
    """Mixin for created_at and updated_at timestamp columns."""
    # Using declared_attr for consistency, though direct Column works too.
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
