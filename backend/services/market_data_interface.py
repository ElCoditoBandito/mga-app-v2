# backend/services/market_data_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date, datetime
from backend.schemas.market_data import (
    EquityQuote,
    HistoricalPricePoint,
    IntradayPricePoint, # Added IntradayPricePoint
    CompanyProfile,
    DividendData,
    StockSplitData,
    OptionQuote,
    ForexQuote,
    CryptoQuote,
    IndexQuote,
    MarketMover,
    MarketAssetType,
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

class MarketDataServiceInterface(ABC):
    """
    Interface for a service that provides market data from various external APIs.
    All methods should be asynchronous and return our canonical Pydantic models.
    """

    @abstractmethod
    async def get_equity_quote(self, symbol: str, exchange: Optional[str] = None) -> Optional[EquityQuote]:
        """Fetch a real-time or delayed quote for an equity (stock, ETF)."""
        pass

    @abstractmethod
    async def get_historical_price_data(
        self,
        symbol: str,
        from_date: date,
        to_date: date,
        exchange: Optional[str] = None
    ) -> List[HistoricalPricePoint]:
        """Fetch historical price data for an equity."""
        pass

    @abstractmethod
    async def get_intraday_price_data(
        self,
        symbol: str,
        interval: str, # e.g., "1min", "5min", "1hour"
        from_date: Optional[datetime] = None, # For specific day/time range
        to_date: Optional[datetime] = None,   # For specific day/time range
        exchange: Optional[str] = None
    ) -> List[IntradayPricePoint]:
        """Fetch intraday price data for an equity."""
        pass

    @abstractmethod
    async def get_company_profile(
        self, 
        symbol: str, 
        exchange: Optional[str] = None
    ) -> Optional[CompanyProfile]:
        """Fetch company profile information."""
        pass

    @abstractmethod
    async def get_dividend_data(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        exchange: Optional[str] = None
    ) -> List[DividendData]:
        """Fetch dividend payment history for an equity."""
        pass
    
    @abstractmethod
    async def get_stock_split_data(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        exchange: Optional[str] = None
    ) -> List[StockSplitData]:
        """Fetch stock split history for an equity."""
        pass

    @abstractmethod
    async def get_option_quote(
        self, 
        contract_symbol: str
    ) -> Optional[OptionQuote]:
        """Fetch a quote for an options contract."""
        pass

    @abstractmethod
    async def get_forex_quote(self, base_currency: str, quote_currency: str) -> Optional[ForexQuote]:
        """Fetch a quote for a Forex pair."""
        pass

    @abstractmethod
    async def get_crypto_quote(self, base_asset: str, quote_asset: str) -> Optional[CryptoQuote]:
        """Fetch a quote for a cryptocurrency pair."""
        pass

    @abstractmethod
    async def get_index_quote(self, symbol: str, exchange: Optional[str] = None) -> Optional[IndexQuote]:
        """Fetch a quote for a market index."""
        pass
    
    @abstractmethod
    async def get_market_movers(
        self, 
        market_segment: str,
        top_n: int = 10,
        exchange: Optional[str] = None 
    ) -> List[MarketMover]:
        """Fetch top market movers (e.g., gainers, losers)."""
        pass

    @abstractmethod
    async def search_symbols(self, query: str, asset_type: Optional[MarketAssetType] = None, limit: int = 10) -> List[CompanyProfile]:
        """Search for symbols/companies based on a query string."""
        pass

    # Phase 2 - Commodity Prices
    @abstractmethod
    async def get_commodity_price(self, commodity_name: str) -> Optional[CommodityPrice]:
        """Fetch current commodity price."""
        pass

    # Phase 2 - Historical Commodity Prices
    @abstractmethod
    async def get_historical_commodity_prices(
        self, 
        commodity_name: str, 
        date_from: Optional[date] = None, 
        date_to: Optional[date] = None, 
        frequency: Optional[str] = None
    ) -> Optional[HistoricalCommodityPriceData]:
        """Fetch historical commodity prices."""
        pass

    # Phase 2 - Company Ratings
    @abstractmethod
    async def get_company_ratings(
        self, 
        ticker: str, 
        date_from: Optional[date] = None, 
        date_to: Optional[date] = None, 
        rated: Optional[str] = None
    ) -> Optional[CompanyRatingData]:
        """Fetch company analyst ratings."""
        pass

    # Phase 2 - Stock Market Index Listing
    @abstractmethod
    async def list_stock_market_indexes(self, limit: int = 100, offset: int = 0) -> List[IndexBasicInfo]:
        """Fetch a list of all available stock market indexes/benchmarks."""
        pass

    # Phase 2 - Bonds Data
    @abstractmethod
    async def list_bond_countries(self, limit: int = 100, offset: int = 0) -> List[BondCountry]:
        """Fetch list of bond-issuing countries."""
        pass

    @abstractmethod
    async def get_bond_info(self, country: str) -> Optional[BondInfoData]:
        """Fetch specific bond info for a country."""
        pass

    # Phase 2 - ETF Data
    @abstractmethod
    async def list_etfs(self, limit: int = 100, offset: int = 0) -> List[ETFTicker]:
        """Fetch a list of ETFs."""
        pass

    @abstractmethod
    async def get_etf_holdings(
        self, 
        ticker: str, 
        date_from: Optional[date] = None, 
        date_to: Optional[date] = None
    ) -> Optional[ETFHoldingDetails]:
        """Fetch detailed ETF holdings."""
        pass
