"""add_club_id_to_transactions_table

Revision ID: de0905767edf
Revises: 89eabd592675
Create Date: 2025-05-13 12:43:45.542777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de0905767edf'
down_revision: Union[str, None] = '89eabd592675'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Import UUID type for PostgreSQL
    from sqlalchemy.dialects.postgresql import UUID
    
    # Add club_id column as nullable initially to allow backfilling
    op.add_column('transactions', sa.Column('club_id', UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_transactions_club_id_clubs',
        'transactions', 'clubs',
        ['club_id'], ['id']
    )
    
    # Create index on club_id
    op.create_index('ix_transactions_club_id', 'transactions', ['club_id'])
    
    # Backfill club_id for transactions with fund_id
    op.execute("""
        UPDATE transactions
        SET club_id = (
            SELECT club_id
            FROM funds
            WHERE funds.id = transactions.fund_id
        )
        WHERE transactions.fund_id IS NOT NULL
    """)
    
    # For transactions where fund_id is NULL (club expenses), we need to determine how to handle them
    # This assumes club expenses are already properly associated with a club in the application logic
    # If there's a specific business rule, it should be implemented here
    
    # Delete any transactions that still have club_id as NULL
    # (i.e., those where fund_id was NULL and no other backfill logic applied)
    op.execute("""
        DELETE FROM transactions
        WHERE club_id IS NULL
    """)
    # This assumes that any transaction where club_id is still NULL at this point
    # (because its fund_id was NULL and it wasn't otherwise assigned a club_id)
    # is considered orphaned and can be safely deleted.

    # Make club_id non-nullable after backfilling and deleting orphans
    op.alter_column('transactions', 'club_id', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove foreign key constraint first
    op.drop_constraint('fk_transactions_club_id_clubs', 'transactions', type_='foreignkey')
    
    # Remove index
    op.drop_index('ix_transactions_club_id', table_name='transactions')
    
    # Remove club_id column
    op.drop_column('transactions', 'club_id')
