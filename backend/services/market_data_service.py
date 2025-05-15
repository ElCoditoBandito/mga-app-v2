from datetime import date, datetime
from typing import List, Optional, Any

from backend.schemas.market_data import (
    StockQuote,
    StockHistoricalData,
    IndexQuote,
    ForexRate,
    # Phase 2 additions
    CommodityPrice,
    HistoricalCommodityPriceData,
    CompanyRatingData,
    IndexBasicInfo,
    BondCountry,
    BondInfoData,
    ETFTicker,
    ETFHoldingDetails
)
from backend.services.market_data_interface import MarketDataServiceInterface
from backend.services.market_data_providers.marketstack_adapter import MarketStackAdapter


class MarketDataService:
    """Service for retrieving market data"""

    def __init__(self, provider: Optional[MarketDataServiceInterface] = None):
        self.provider = provider or MarketStackAdapter()

    async def get_stock_quote(self, symbol: str) -> Optional[StockQuote]:
        """Get current stock quote for a symbol"""
        return await self.provider.get_stock_quote(symbol)

    async def get_stock_historical_data(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> Optional[StockHistoricalData]:
        """Get historical stock data for a symbol"""
        return await self.provider.get_stock_historical_data(
            symbol, from_date, to_date
        )

    async def get_index_quote(self, symbol: str) -> Optional[IndexQuote]:
        """Get current quote for a market index"""
        return await self.provider.get_index_quote(symbol)

    async def get_forex_rate(
        self, base_currency: str, quote_currency: str
    ) -> Optional[ForexRate]:
        """Get current forex exchange rate"""
        return await self.provider.get_forex_rate(base_currency, quote_currency)

    # Phase 2 - Commodity Prices
    async def get_commodity_price(self, commodity_name: str) -> Optional[CommodityPrice]:
        """Get current commodity price"""
        return await self.provider.get_commodity_price(commodity_name)

    # Phase 2 - Historical Commodity Prices
    async def get_historical_commodity_prices(
        self, 
        commodity_name: str, 
        date_from: Optional[date] = None, 
        date_to: Optional[date] = None, 
        frequency: Optional[str] = None
    ) -> Optional[HistoricalCommodityPriceData]:
        """Get historical commodity prices"""
        return await self.provider.get_historical_commodity_prices(
            commodity_name, date_from, date_to, frequency
        )

    # Phase 2 - Company Ratings
    async def get_company_ratings(
        self, 
        ticker: str, 
        date_from: Optional[date] = None, 
        date_to: Optional[date] = None, 
        rated: Optional[str] = None
    ) -> Optional[CompanyRatingData]:
        """Get company analyst ratings"""
        return await self.provider.get_company_ratings(
            ticker, date_from, date_to, rated
        )

    # Phase 2 - Stock Market Index Listing
    async def list_stock_market_indexes(
        self, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[IndexBasicInfo]:
        """Get a list of all available stock market indexes/benchmarks"""
        return await self.provider.list_stock_market_indexes(limit, offset)

    # Phase 2 - Bonds Data
    async def list_bond_countries(
        self, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[BondCountry]:
        """Get a list of bond-issuing countries"""
        return await self.provider.list_bond_countries(limit, offset)

    async def get_bond_info(self, country: str) -> Optional[BondInfoData]:
        """Get specific bond info for a country"""
        return await self.provider.get_bond_info(country)

    # Phase 2 - ETF Data
    async def list_etfs(
        self, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[ETFTicker]:
        """Get a list of ETFs"""
        return await self.provider.list_etfs(limit, offset)

    async def get_etf_holdings(
        self, 
        ticker: str, 
        date_from: Optional[date] = None, 
        date_to: Optional[date] = None
    ) -> Optional[ETFHoldingDetails]:
        """Get detailed ETF holdings"""
        return await self.provider.get_etf_holdings(ticker, date_from, date_to)
