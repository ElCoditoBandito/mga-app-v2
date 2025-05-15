from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.schemas.market_data import (
    StockQuoteResponse,
    StockHistoricalDataResponse,
    IndexQuoteResponse,
    ForexRateResponse,
    # Phase 2 additions
    CommodityPriceResponse,
    HistoricalCommodityPriceResponse,
    CompanyRatingResponse,
    IndexListResponse,
    BondCountryListResponse,
    BondInfoResponse,
    ETFTickerListResponse,
    ETFHoldingResponse
)
from backend.services.market_data_service import MarketDataService

router = APIRouter(prefix="/market-data", tags=["market-data"])


@router.get("/stocks/{symbol}", response_model=StockQuoteResponse)
async def get_stock_quote(
    symbol: str,
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
):
    """Get current stock quote for a symbol"""
    quote = await market_data_service.get_stock_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Stock quote for {symbol} not found")
    return StockQuoteResponse(data=quote)


@router.get("/stocks/{symbol}/historical", response_model=StockHistoricalDataResponse)
async def get_stock_historical_data(
    symbol: str,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
):
    """Get historical stock data for a symbol"""
    data = await market_data_service.get_stock_historical_data(
        symbol, from_date, to_date
    )
    if not data:
        raise HTTPException(
            status_code=404, detail=f"Historical data for {symbol} not found"
        )
    return StockHistoricalDataResponse(data=data)


@router.get("/indices/{symbol}", response_model=IndexQuoteResponse)
async def get_index_quote(
    symbol: str,
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
):
    """Get current quote for a market index"""
    quote = await market_data_service.get_index_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Index quote for {symbol} not found")
    return IndexQuoteResponse(data=quote)


@router.get("/forex", response_model=ForexRateResponse)
async def get_forex_rate(
    base: str,
    quote: str,
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
):
    """Get current forex exchange rate"""
    rate = await market_data_service.get_forex_rate(base, quote)
    if not rate:
        raise HTTPException(
            status_code=404, detail=f"Forex rate for {base}/{quote} not found"
        )
    return ForexRateResponse(data=rate)


# Phase 2 - Commodity Prices
@router.get("/commodities/{commodity_name}", response_model=CommodityPriceResponse)
async def get_commodity_price(
    commodity_name: str,
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
):
    """
    Get current commodity price
    
    Note: Requires Professional plan or higher. Rate limit 1 call/min.
    """
    price = await market_data_service.get_commodity_price(commodity_name)
    if not price:
        raise HTTPException(
            status_code=404, detail=f"Commodity price for {commodity_name} not found"
        )
    return CommodityPriceResponse(data=price)


# Phase 2 - Historical Commodity Prices
@router.get("/commodities/{commodity_name}/historical", response_model=HistoricalCommodityPriceResponse)
async def get_historical_commodity_prices(
    commodity_name: str,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    frequency: Optional[str] = Query(None, description="Data frequency (daily, weekly, monthly)"),
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
):
    """
    Get historical commodity prices
    
    Note: Requires Professional plan or higher. Rate limit 1 call/min. Max 1-year range for daily data.
    """
    data = await market_data_service.get_historical_commodity_prices(
        commodity_name, from_date, to_date, frequency
    )
    if not data:
        raise HTTPException(
            status_code=404, detail=f"Historical commodity prices for {commodity_name} not found"
        )
    return HistoricalCommodityPriceResponse(data=data)


# Phase 2 - Company Ratings
@router.get("/companies/{ticker}/ratings", response_model=CompanyRatingResponse)
async def get_company_ratings(
    ticker: str,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    rated: Optional[str] = Query(None, description="Filter by rating (buy, sell, hold)"),
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
):
    """
    Get company analyst ratings
    
    Note: Requires Business plan or higher. Rate limit 1 call/min.
    """
    ratings = await market_data_service.get_company_ratings(
        ticker, from_date, to_date, rated
    )
    if not ratings:
        raise HTTPException(
            status_code=404, detail=f"Company ratings for {ticker} not found"
        )
    return CompanyRatingResponse(data=ratings)


# Phase 2 - Stock Market Index Listing
@router.get("/indices", response_model=IndexListResponse)
async def list_stock_market_indexes(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
):
    """
    Get a list of all available stock market indexes/benchmarks
    
    Note: Available on Basic plan and higher.
    """
    indexes = await market_data_service.list_stock_market_indexes(limit, offset)
    return IndexListResponse(data=indexes)


# Phase 2 - Bonds Data
@router.get("/bonds", response_model=BondCountryListResponse)
async def list_bond_countries(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
):
    """
    Get a list of bond-issuing countries
    
    Note: Available on Basic plan and higher.
    """
    countries = await market_data_service.list_bond_countries(limit, offset)
    return BondCountryListResponse(data=countries)


@router.get("/bonds/{country}", response_model=BondInfoResponse)
async def get_bond_info(
    country: str,
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
):
    """
    Get specific bond info for a country
    
    Note: Available on Basic plan and higher.
    """
    bond_info = await market_data_service.get_bond_info(country)
    if not bond_info:
        raise HTTPException(
            status_code=404, detail=f"Bond info for {country} not found"
        )
    return BondInfoResponse(data=bond_info)


# Phase 2 - ETF Data
@router.get("/etfs", response_model=ETFTickerListResponse)
async def list_etfs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
):
    """
    Get a list of ETFs
    
    Note: Available on Basic plan and higher. CALL COUNT MULTIPLIER of 20 for ETF endpoints.
    """
    etfs = await market_data_service.list_etfs(limit, offset)
    return ETFTickerListResponse(data=etfs)


@router.get("/etfs/{ticker}/holdings", response_model=ETFHoldingResponse)
async def get_etf_holdings(
    ticker: str,
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    market_data_service: MarketDataService = Depends(lambda: MarketDataService()),
):
    """
    Get detailed ETF holdings
    
    Note: Available on Basic plan and higher. CALL COUNT MULTIPLIER of 20 for ETF endpoints.
    """
    holdings = await market_data_service.get_etf_holdings(ticker, from_date, to_date)
    if not holdings:
        raise HTTPException(
            status_code=404, detail=f"ETF holdings for {ticker} not found"
        )
    return ETFHoldingResponse(data=holdings)
