# backend/api/v1/__init__.py

from fastapi import APIRouter

# Import endpoint routers
from .endpoints import users, clubs, assets, transactions # Add others as they are created

# Create the v1 router
api_router = APIRouter()

# Include endpoint routers with tags for OpenAPI documentation
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(clubs.router, prefix="/clubs", tags=["Clubs"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(transactions.router, prefix="/clubs/{club_id}/transactions", tags=["Transactions"])
# Include other routers here (e.g., transactions, members if separated)

