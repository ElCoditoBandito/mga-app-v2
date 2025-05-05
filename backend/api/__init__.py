# backend/api/__init__.py

from fastapi import APIRouter

# Import the v1 router
from .v1 import api_router as api_v1_router

# Create the main API router
api_router = APIRouter()

# Include the v1 router WITHOUT an additional prefix here
# The "/api/v1" prefix is applied in main.py
api_router.include_router(api_v1_router) # Removed prefix="/v1"

# You could add other versions (e.g., v2) here later
# from .v2 import api_router as api_v2_router
# api_router.include_router(api_v2_router, prefix="/v2") # Add prefix for other versions if needed

