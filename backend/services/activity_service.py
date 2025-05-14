import uuid
from typing import Sequence, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.activity import ActivityFeedItem
from backend.crud import transaction as crud_transaction
from backend.crud import member_transaction as crud_member_transaction
from backend.models.enums import TransactionType, MemberTransactionType

async def get_club_activity_feed(
    db: AsyncSession, *, club_id: uuid.UUID, limit: int = 10
) -> Sequence[ActivityFeedItem]:
    """
    Get a combined activity feed for a club, including both general transactions
    and member transactions, sorted by date.
    """
    # Fetch a buffer of transactions to ensure we have enough after merging and sorting
    buffer_limit = limit * 2

    # Fetch club transactions
    transactions = await crud_transaction.get_multi_transactions(
        db, club_id=club_id, skip=0, limit=buffer_limit
    )

    # Fetch member transactions
    member_transactions = await crud_member_transaction.get_multi_by_club_id(
        db, club_id=club_id, skip=0, limit=buffer_limit
    )

    # Transform transactions to ActivityFeedItems
    activity_items: List[ActivityFeedItem] = []

    # Process general transactions
    for tx in transactions:
        item_type = str(tx.transaction_type.value)
        
        activity_items.append(
            ActivityFeedItem(
                id=tx.id,
                activity_date=tx.transaction_date,
                item_type=item_type,
                description=tx.description or "",
                amount=tx.total_amount,
                asset_symbol=tx.asset.symbol if tx.asset else None,
                fund_name=tx.fund.name if tx.fund else None,
            )
        )

    # Process member transactions
    for mtx in member_transactions:
        item_type = str(mtx.transaction_type.value)
        user = mtx.membership.user if mtx.membership else None
        user_name = f"{user.first_name} {user.last_name}" if user else None
        
        activity_items.append(
            ActivityFeedItem(
                id=mtx.id,
                activity_date=mtx.transaction_date,
                item_type=item_type,
                description=mtx.notes or "",
                amount=mtx.amount,
                user_name=user_name,
            )
        )

    # Sort all items by date (newest first) and limit the result
    activity_items.sort(key=lambda x: x.activity_date, reverse=True)
    return activity_items[:limit]