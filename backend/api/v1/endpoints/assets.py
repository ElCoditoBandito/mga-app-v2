# backend/api/v1/endpoints/assets.py

import uuid
import logging
from typing import List, Any, Sequence # Added Sequence

# Assuming FastAPI and related libraries are installed
try:
    from fastapi import APIRouter, Depends, HTTPException, status, Path, Query, Body
    from sqlalchemy.ext.asyncio import AsyncSession
except ImportError:
    print("WARNING: FastAPI or SQLAlchemy not found. API endpoints will not work.")
    # Define dummy types/classes if needed
    class APIRouter:
        def post(self, *args, **kwargs): pass
        def get(self, *args, **kwargs): pass
    def Depends(dependency: Any | None = None) -> Any: return None
    class HTTPException(Exception): pass
    class Status: HTTP_201_CREATED = 201; HTTP_500_INTERNAL_SERVER_ERROR = 500; HTTP_404_NOT_FOUND = 404; HTTP_403_FORBIDDEN = 403; HTTP_400_BAD_REQUEST = 400; HTTP_409_CONFLICT = 409; HTTP_200_OK = 200; HTTP_422_UNPROCESSABLE_ENTITY = 422
    status = Status()
    def Path(*args, **kwargs): return uuid.uuid4()
    def Query(*args, **kwargs): return None
    def Body(*args, **kwargs): return None
    class AsyncSession: pass

# Import dependencies, schemas, services, models
try:
    from backend.api.dependencies import get_db_session, get_current_active_user
    from backend.schemas import AssetRead, AssetCreateStock, AssetCreateOption # Import asset schemas
    from backend.services import asset_service # Import the relevant service
    from backend.models import User, Asset # Import User and Asset models
except ImportError as e:
    print(f"WARNING: Failed to import dependencies/schemas/services: {e}. Asset endpoints may not work.")
    # Define dummy types/classes if needed
    async def get_db_session() -> AsyncSession: return AsyncSession()
    async def get_current_active_user() -> User: return User(id=uuid.uuid4(), is_active=True, auth0_sub="dummy|sub")
    class AssetRead: pass
    class AssetCreateStock: pass
    class AssetCreateOption: pass
    class User: id: uuid.UUID; is_active: bool; auth0_sub: str = "dummy|sub"
    class Asset: pass # Dummy model
    class asset_service:
        @staticmethod
        async def get_or_create_stock_asset(db: AsyncSession, *, asset_in: AssetCreateStock) -> Asset: return Asset()
        @staticmethod
        async def get_or_create_option_asset(db: AsyncSession, *, asset_in: AssetCreateOption) -> Asset: return Asset()
        @staticmethod
        async def list_assets(db: AsyncSession, *, skip: int = 0, limit: int = 100) -> Sequence[Asset]: return [Asset()]
        @staticmethod
        async def get_asset_by_id(db: AsyncSession, asset_id: uuid.UUID) -> Asset: return Asset()


# Configure logging
log = logging.getLogger(__name__)

# Create router instance
router = APIRouter()


@router.post(
    "/stock",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Get or Create Stock Asset",
    description="Retrieves a stock asset by symbol or creates it if it doesn't exist. Accessible by any authenticated user.",
)
async def get_or_create_stock(
    asset_data: AssetCreateStock = Body(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user) # Ensure user is authenticated
):
    """
    API endpoint to get or create a stock asset definition.
    """
    log.info(f"Received request to get/create stock asset with symbol '{asset_data.symbol}' by user {current_user.id}")
    try:
        asset = await asset_service.get_or_create_stock_asset(db=db, asset_in=asset_data) # [cite: asset_service_code]
        log.info(f"Successfully retrieved/created stock asset {asset.id} for symbol '{asset_data.symbol}'")
        return asset
    except HTTPException as e:
        raise e
    except Exception as e:
        log.exception(f"Unexpected error getting/creating stock asset '{asset_data.symbol}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing the stock asset.",
        )


@router.post(
    "/option",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Get or Create Option Asset",
    description="Retrieves an option asset by its details or creates it if it doesn't exist (requires underlying stock to exist). Accessible by any authenticated user.",
)
async def get_or_create_option(
    asset_data: AssetCreateOption = Body(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user) # Ensure user is authenticated
):
    """
    API endpoint to get or create an option asset definition.
    """
    log.info(f"Received request to get/create option asset for underlying '{asset_data.underlying_symbol}' by user {current_user.id}")
    try:
        asset = await asset_service.get_or_create_option_asset(db=db, asset_in=asset_data) # [cite: asset_service_code]
        log.info(f"Successfully retrieved/created option asset {asset.id} for underlying '{asset_data.underlying_symbol}'")
        return asset
    except HTTPException as e:
        raise e
    except Exception as e:
        log.exception(f"Unexpected error getting/creating option asset for underlying '{asset_data.underlying_symbol}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing the option asset.",
        )


@router.get(
    "",
    response_model=List[AssetRead],
    summary="List Assets",
    description="Retrieves a paginated list of all defined assets (stocks and options). Accessible by any authenticated user.",
)
async def list_all_assets(
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user) # Ensure user is authenticated
):
    """
    API endpoint to list all assets.
    """
    log.info(f"Received request to list assets (skip={skip}, limit={limit}) by user {current_user.id}")
    try:
        assets = await asset_service.list_assets(db=db, skip=skip, limit=limit) # [cite: asset_service_code]
        log.info(f"Retrieved {len(assets)} assets.")
        return assets
    except Exception as e:
        log.exception(f"Unexpected error listing assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while listing assets.",
        )


@router.get(
    "/{asset_id}",
    response_model=AssetRead,
    summary="Get Asset Details",
    description="Retrieves details for a specific asset by its ID. Accessible by any authenticated user.",
)
async def get_asset_details(
    asset_id: uuid.UUID = Path(..., title="The ID of the asset to retrieve"),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_active_user) # Ensure user is authenticated
):
    """
    API endpoint to get details for a specific asset.
    """
    log.info(f"Received request for details of asset {asset_id} by user {current_user.id}")
    try:
        asset = await asset_service.get_asset_by_id(db=db, asset_id=asset_id) # [cite: asset_service_code]
        # Service raises 404 if not found
        log.info(f"Successfully retrieved asset {asset_id}")
        return asset
    except HTTPException as e:
        raise e
    except Exception as e:
        log.exception(f"Unexpected error retrieving asset {asset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while retrieving the asset.",
        )

# ---Add new assets endpoints here ---