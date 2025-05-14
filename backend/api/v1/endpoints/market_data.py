# backend/api/v1/endpoints/market_data.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import date

from backend.schemas.market_data import (
    EquityQuote,
    HistoricalPricePoint,
    CompanyProfile,
    NewsArticle,
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
    # Depending on provider, an empty list might be a valid response if no data for the range.
    # Only raise 404 if symbol itself is definitively not found, which is harder to tell from just historical data.
    # if not historical_data: 
    #     raise HTTPException(status_code=404, detail=f"Historical data not found for symbol {symbol}")
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

@router.get(
    "/news",
    response_model=List[NewsArticle],
    summary="Get Market News",
    tags=["Market Data"]
)
async def read_market_news(
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols (e.g., AAPL,MSFT)"),
    limit: int = Query(20, ge=1, le=100, description="Number of articles to return"),
    # 'source' for MarketStack is like "-CNBC,Reuters"
    source: Optional[str] = Query(None, description="Filter by news source(s), provider-specific format"), 
    market_service: MarketDataService = Depends(get_market_data_service)
):
    """
    Retrieve market news articles. Can be filtered by symbols.
    """
    symbol_list = symbols.split(',') if symbols else None
    news = await market_service.get_news_articles(symbols=symbol_list, limit=limit, source=source)
    return news

# Add more endpoints here for other MarketDataService methods as needed.
