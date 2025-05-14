# backend/services/market_data_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import date, datetime
from backend.schemas.market_data import (
    EquityQuote,
    HistoricalPricePoint,
    CompanyProfile,
    NewsArticle,
    DividendData,
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
    async def get_company_profile(
        self, 
        symbol: str, 
        exchange: Optional[str] = None
    ) -> Optional[CompanyProfile]:
        """Fetch company profile information."""
        pass

    @abstractmethod
    async def get_news_articles(
        self,
        symbols: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        limit: int = 20,
        source: Optional[str] = None # e.g. specific news provider
    ) -> List[NewsArticle]:
        """Fetch news articles, filterable by symbols, topics, or all general news."""
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

    # --- Optional methods for other asset types based on initial models ---
    # Implement these as needed for your MVP or future enhancements

    @abstractmethod
    async def get_option_quote(
        self, 
        contract_symbol: str # Specific option contract symbol
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
        market_segment: str, # e.g., 'gainers', 'losers', 'most_active'
        top_n: int = 10,
        exchange: Optional[str] = None 
    ) -> List[MarketMover]:
        """Fetch top market movers (e.g., gainers, losers)."""
        pass

    @abstractmethod
    async def search_symbols(self, query: str, asset_type: Optional[MarketAssetType] = None, limit: int = 10) -> List[CompanyProfile]:
        """Search for symbols/companies based on a query string."""
        pass

