# backend/api/v1/endpoints/market_data.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import date # Ensure date is imported

from backend.schemas.market_data import (
    EquityQuote,
    HistoricalPricePoint,
    CompanyProfile,
    # NewsArticle, # Removed NewsArticle import
    DividendData,
    StockSplitData,
    IndexQuote,
    MarketAssetType,
    # Add other schemas as you create endpoints for them
)
from backend.services.market_data_service import MarketDataService
# We'll need a way to get the MarketDataService instance. Let's define a dependency.

# Placeholder for API key loading if needed directly by service constructor
# In a real app, use a proper config management (e.g., Pydantic BaseSettings)
# For now, the MarketDataService and its adapters load keys from os.getenv()

async def get_market_data_service():
    """FastAPI dependency to get an instance of MarketDataService."""
    # API keys are loaded from environment variables by the adapters themselves for now.
    service = MarketDataService(provider="marketstack") 
    try:
        yield service
    finally:
        await service.close_adapter() # Ensure the adapter's resources are cleaned up

router = APIRouter()

@router.get(
    "/quote/{symbol}", 
    response_model=Optional[EquityQuote],
    summary="Get Equity Quote",
    tags=["Market Data"]
)
async def read_equity_quote(
    symbol: str,
    exchange: Optional[str] = Query(None, description="Optional exchange symbol (e.g., XNAS for NASDAQ)"),
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Retrieve the latest available quote for a given equity symbol.
    """
    quote = await market_service.get_equity_quote(symbol=symbol, exchange=exchange)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Quote not found for symbol {symbol}")
    return quote

@router.get(
    "/historical/{symbol}",
    response_model=List[HistoricalPricePoint],
    summary="Get Historical Price Data",
    tags=["Market Data"]
)
async def read_historical_price_data(
    symbol: str,
    from_date: date = Query(..., description="Start date in YYYY-MM-DD format"),
    to_date: date = Query(..., description="End date in YYYY-MM-DD format"),
    exchange: Optional[str] = Query(None, description="Optional exchange symbol"),
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Retrieve historical end-of-day price data for a given equity symbol between two dates.
    """
    historical_data = await market_service.get_historical_price_data(
        symbol=symbol,
        from_date=from_date,
        to_date=to_date,
        exchange=exchange
    )
    return historical_data

@router.get(
    "/profile/{symbol}",
    response_model=Optional[CompanyProfile],
    summary="Get Company Profile",
    tags=["Market Data"]
)
async def read_company_profile(
    symbol: str,
    exchange: Optional[str] = Query(None, description="Optional exchange symbol"),
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Retrieve company profile information for a given equity symbol.
    """
    profile = await market_service.get_company_profile(symbol=symbol, exchange=exchange)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile not found for symbol {symbol}")
    return profile

# News endpoint removed as MarketStack v2 does not seem to support it directly.
# @router.get(
#     "/news",
#     response_model=List[NewsArticle],
#     summary="Get Market News",
#     tags=["Market Data"]
# )
# async def read_market_news(
#     symbols: Optional[str] = Query(None, description="Comma-separated list of symbols (e.g., AAPL,MSFT)"),
#     limit: int = Query(20, ge=1, le=100, description="Number of articles to return"),
#     source: Optional[str] = Query(None, description="Filter by news source(s), provider-specific format"), 
#     market_service: MarketDataService = Depends(get_market_data_service)
# ):
#     """
#     Retrieve market news articles. Can be filtered by symbols.
#     """
#     symbol_list = symbols.split(',') if symbols else None
#     news = await market_service.get_news_articles(symbols=symbol_list, limit=limit, source=source)
#     return news

@router.get(
    "/{symbol}/dividends",
    response_model=List[DividendData],
    summary="Get Dividend Data",
    tags=["Market Data"]
)
async def read_dividend_data(
    symbol: str,
    from_date: Optional[date] = Query(None, description="Start date in YYYY-MM-DD format (optional)"),
    to_date: Optional[date] = Query(None, description="End date in YYYY-MM-DD format (optional)"),
    exchange: Optional[str] = Query(None, description="Optional exchange symbol for disambiguation (e.g., XNAS)"),
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Retrieve dividend history for a given equity symbol.
    Can be filtered by a date range.
    """
    dividends = await market_service.get_dividend_data(
        symbol=symbol,
        from_date=from_date,
        to_date=to_date,
        exchange=exchange
    )
    return dividends

@router.get(
    "/{symbol}/splits",
    response_model=List[StockSplitData],
    summary="Get Stock Split History",
    tags=["Market Data"]
)
async def read_stock_split_data(
    symbol: str,
    from_date: Optional[date] = Query(None, description="Start date in YYYY-MM-DD format (optional)"),
    to_date: Optional[date] = Query(None, description="End date in YYYY-MM-DD format (optional)"),
    exchange: Optional[str] = Query(None, description="Optional exchange symbol for disambiguation (e.g., XNAS)"),
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Retrieve stock split history for a given equity symbol.
    Can be filtered by a date range.
    """
    splits = await market_service.get_stock_split_data(
        symbol=symbol,
        from_date=from_date,
        to_date=to_date,
        exchange=exchange
    )
    return splits

@router.get(
    "/index/{symbol}",
    response_model=Optional[IndexQuote],
    summary="Get Index Quote",
    tags=["Market Data"]
)
async def read_index_quote(
    symbol: str,
    exchange: Optional[str] = Query(None, description="Optional exchange symbol for the index (if applicable by provider)"),
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Retrieve the latest available quote for a given market index symbol.
    """
    index_quote = await market_service.get_index_quote(symbol=symbol, exchange=exchange)
    if not index_quote:
        raise HTTPException(status_code=404, detail=f"Index quote not found for symbol {symbol}")
    return index_quote

@router.get(
    "/search",
    response_model=List[CompanyProfile], # Assuming search returns a list of company profiles
    summary="Search for Symbols/Companies",
    tags=["Market Data"]
)
async def search_symbols_companies(
    query_str: str = Query(..., alias="query", description="Search query string (e.g., company name or symbol fragment)"),
    asset_type: Optional[MarketAssetType] = Query(None, description="Filter by asset type (e.g., STOCK, ETF)"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results to return"),
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Search for market symbols or companies based on a query string.
    The MarketStackAdapter uses the /tickerslist endpoint which returns basic company info,
    so CompanyProfile is used as the response model here.
    """
    results = await market_service.search_symbols(query=query_str, asset_type=asset_type, limit=limit)
    return results

# Add more endpoints here for other MarketDataService methods as needed.
