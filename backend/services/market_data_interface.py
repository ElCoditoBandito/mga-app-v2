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
    MarketAssetType
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
