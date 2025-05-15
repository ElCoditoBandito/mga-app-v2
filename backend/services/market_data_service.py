# backend/services/market_data_service.py
from typing import List, Optional
from datetime import date, datetime

from backend.schemas.market_data import (
    EquityQuote,
    HistoricalPricePoint,
    CompanyProfile,
    # NewsArticle, # Removed NewsArticle import if it's not used by other methods
    DividendData,
    StockSplitData,
    OptionQuote,
    ForexQuote,
    CryptoQuote,
    IndexQuote,
    MarketMover,
    MarketAssetType
)
from backend.services.market_data_interface import MarketDataServiceInterface
from backend.services.market_data_providers.marketstack_adapter import MarketStackAdapter
# Import other adapters here as they are created, e.g.:
# from backend.services.market_data_providers.alphavantage_adapter import AlphaVantageAdapter

class MarketDataService(MarketDataServiceInterface):
    """
    Main service for accessing market data.
    It uses a configured adapter (e.g., MarketStackAdapter) to fetch the data.
    This class implements the MarketDataServiceInterface and delegates calls
    to the active provider adapter.
    """

    def __init__(self, provider: str = "marketstack", api_key_marketstack: Optional[str] = None, api_key_alphavantage: Optional[str] = None):
        self.provider_name = provider
        self._adapter: MarketDataServiceInterface

        if self.provider_name == "marketstack":
            self._adapter = MarketStackAdapter(api_key=api_key_marketstack)
        # elif self.provider_name == "alphavantage":
        #     self._adapter = AlphaVantageAdapter(api_key=api_key_alphavantage)
        else:
            raise ValueError(f"Unsupported market data provider: {self.provider_name}")
        
        print(f"MarketDataService initialized with provider: {self.provider_name}")

    async def get_equity_quote(self, symbol: str, exchange: Optional[str] = None) -> Optional[EquityQuote]:
        return await self._adapter.get_equity_quote(symbol, exchange)

    async def get_historical_price_data(
        self,
        symbol: str,
        from_date: date,
        to_date: date,
        exchange: Optional[str] = None
    ) -> List[HistoricalPricePoint]:
        return await self._adapter.get_historical_price_data(symbol, from_date, to_date, exchange)

    async def get_company_profile(
        self, 
        symbol: str, 
        exchange: Optional[str] = None
    ) -> Optional[CompanyProfile]:
        return await self._adapter.get_company_profile(symbol, exchange)

    # get_news_articles method removed

    async def get_dividend_data(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        exchange: Optional[str] = None
    ) -> List[DividendData]:
        return await self._adapter.get_dividend_data(symbol, from_date, to_date, exchange)

    async def get_stock_split_data(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        exchange: Optional[str] = None
    ) -> List[StockSplitData]:
        return await self._adapter.get_stock_split_data(symbol, from_date, to_date, exchange)

    async def get_option_quote(
        self, 
        contract_symbol: str
    ) -> Optional[OptionQuote]:
        return await self._adapter.get_option_quote(contract_symbol)

    async def get_forex_quote(self, base_currency: str, quote_currency: str) -> Optional[ForexQuote]:
        return await self._adapter.get_forex_quote(base_currency, quote_currency)

    async def get_crypto_quote(self, base_asset: str, quote_asset: str) -> Optional[CryptoQuote]:
        return await self._adapter.get_crypto_quote(base_asset, quote_asset)

    async def get_index_quote(self, symbol: str, exchange: Optional[str] = None) -> Optional[IndexQuote]:
        return await self._adapter.get_index_quote(symbol, exchange)
    
    async def get_market_movers(
        self, 
        market_segment: str,
        top_n: int = 10,
        exchange: Optional[str] = None
    ) -> List[MarketMover]:
        return await self._adapter.get_market_movers(market_segment, top_n, exchange)

    async def search_symbols(self, query: str, asset_type: Optional[MarketAssetType] = None, limit: int = 10) -> List[CompanyProfile]:
        return await self._adapter.search_symbols(query, asset_type, limit)

    async def close_adapter(self):
        """
        Closes the underlying adapter's resources, like HTTP client sessions.
        This should be called when the service is done, e.g., on application shutdown.
        """
        if hasattr(self._adapter, 'close') and callable(self._adapter.close):
            await self._adapter.close()
            print(f"MarketDataService adapter ({self.provider_name}) closed.")
        else:
            print(f"MarketDataService adapter ({self.provider_name}) does not have a close method or it is not callable.")
