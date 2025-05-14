"""standardize_enum_string_values

Revision ID: a93f75b8c96f
Revises: de0905767edf
Create Date: 2025-05-13 13:21:45.035620

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a93f75b8c96f'
down_revision: Union[str, None] = 'de0905767edf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # For PostgreSQL enums, we need to:
    # 1. Create a new enum type with the updated values
    # 2. Update the column to use the new enum type
    # 3. Drop the old enum type
    
    # Create a new enum type with the updated values
    op.execute("CREATE TYPE club_role_enum_new AS ENUM ('Admin', 'Member', 'ReadOnly')")
    
    # Create a temporary column with the new enum type
    op.execute("ALTER TABLE club_memberships ADD COLUMN role_new club_role_enum_new")
    
    # Copy data from the old column to the new column with the appropriate mapping
    op.execute("""
        UPDATE club_memberships
        SET role_new = CASE
            WHEN role = 'ADMIN' THEN 'Admin'::club_role_enum_new
            WHEN role = 'MEMBER' THEN 'Member'::club_role_enum_new
            WHEN role = 'READ_ONLY' THEN 'ReadOnly'::club_role_enum_new
        END
    """)
    
    # Drop the old column
    op.execute("ALTER TABLE club_memberships DROP COLUMN role")
    
    # Rename the new column to the original name
    op.execute("ALTER TABLE club_memberships RENAME COLUMN role_new TO role")
    
    # Add NOT NULL constraint if needed
    op.execute("ALTER TABLE club_memberships ALTER COLUMN role SET NOT NULL")
    
    # Drop the old enum type
    op.execute("DROP TYPE club_role_enum")
    
    # Rename the new enum type to the original name
    op.execute("ALTER TYPE club_role_enum_new RENAME TO club_role_enum")


def downgrade() -> None:
    """Downgrade schema."""
    # Reverse the process for downgrade
    
    # Create a new enum type with the original values
    op.execute("CREATE TYPE club_role_enum_old AS ENUM ('ADMIN', 'MEMBER', 'READ_ONLY')")
    
    # Create a temporary column with the old enum type
    op.execute("ALTER TABLE club_memberships ADD COLUMN role_old club_role_enum_old")
    
    # Copy data from the current column to the old column with the appropriate mapping
    op.execute("""
        UPDATE club_memberships
        SET role_old = CASE
            WHEN role = 'Admin' THEN 'ADMIN'::club_role_enum_old
            WHEN role = 'Member' THEN 'MEMBER'::club_role_enum_old
            WHEN role = 'ReadOnly' THEN 'READ_ONLY'::club_role_enum_old
        END
    """)
    
    # Drop the current column
    op.execute("ALTER TABLE club_memberships DROP COLUMN role")
    
    # Rename the old column to the original name
    op.execute("ALTER TABLE club_memberships RENAME COLUMN role_old TO role")
    
    # Add NOT NULL constraint if needed
    op.execute("ALTER TABLE club_memberships ALTER COLUMN role SET NOT NULL")
    
    # Drop the current enum type
    op.execute("DROP TYPE club_role_enum")
    
    # Rename the old enum type to the original name
    op.execute("ALTER TYPE club_role_enum_old RENAME TO club_role_enum")
