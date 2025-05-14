# backend/services/market_data_providers/marketstack_adapter.py
import httpx
import os
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timezone
from backend.services.market_data_interface import MarketDataServiceInterface
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
    MarketAssetType,
    MarketTradingStatus, # Added for mapping if possible
    MarketDataError
)

# It's good practice to load environment variables once or have a config module
MARKET_STACK_API_KEY = os.getenv("MARKET_STACK_API_KEY")
MARKET_STACK_BASE_URL = "http://api.marketstack.com/v1" # Common base URL

class MarketStackAdapter(MarketDataServiceInterface):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or MARKET_STACK_API_KEY
        if not self.api_key:
            raise ValueError("MarketStack API key is required.")
        # HTTP client should be managed carefully in a real app (e.g., singleton or passed in)
        # For simplicity here, we create one per instance or per call.
        # Using a timeout is crucial for production code.
        self.client = httpx.AsyncClient(base_url=MARKET_STACK_BASE_URL, timeout=10.0)

    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Helper method to make requests to MarketStack API."""
        if not self.api_key:
            # This should ideally not happen if constructor checks, but good for safety
            raise MarketDataError(message="MarketStack API key not configured.")

        all_params = params.copy() if params else {}
        all_params["access_key"] = self.api_key

        try:
            response = await self.client.get(endpoint, params=all_params)
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
            return response.json()
        except httpx.TimeoutException as e:
            raise MarketDataError(message=f"MarketStack request timed out: {e}", provider="MarketStack")
        except httpx.HTTPStatusError as e:
            # Attempt to parse error response from MarketStack if available
            error_details = "No specific error details from provider."
            try:
                error_data = e.response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_details = error_data["error"]["message"]
            except Exception:
                pass # Keep generic error if parsing fails
            raise MarketDataError(
                message=f"MarketStack API error: {e.response.status_code} - {error_details}",
                provider="MarketStack",
                errorCode=str(e.response.status_code)
            )
        except httpx.RequestError as e:
            raise MarketDataError(message=f"Error connecting to MarketStack: {e}", provider="MarketStack")
        except Exception as e: # Catch-all for other unexpected errors like JSON decoding
            raise MarketDataError(message=f"An unexpected error occurred with MarketStack: {str(e)}", provider="MarketStack")

    def _map_to_historical_price_point(self, data: Dict[str, Any]) -> HistoricalPricePoint:
        # MarketStack often returns date as string 'YYYY-MM-DDTHH:MM:SS+0000'
        # We need to parse it into a datetime object.
        # For historical EOD, time part might be 00:00:00, but it's safer to parse fully.
        dt_object = datetime.fromisoformat(data["date"].replace("+0000", "+00:00"))

        return HistoricalPricePoint(
            date=dt_object,
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
            adjustedClose=data.get("adj_close"), # MarketStack uses 'adj_close'
            volume=int(data["volume"]) if data["volume"] is not None else 0, # Ensure volume is int
        )

    def _map_to_equity_quote(self, data: Dict[str, Any], symbol_override: Optional[str] = None) -> EquityQuote:
        # MarketStack's EOD data can be used for the latest quote if 'latest' endpoint is used
        # or if we take the first item from a single-day historical request.
        # The 'date' field from MarketStack is a datetime string like '2023-10-27T00:00:00+0000'
        
        # Try to parse timestamp, provide a sensible default if parsing fails or field is missing
        try:
            timestamp = datetime.fromisoformat(data["date"].replace("+0000", "+00:00"))
        except (KeyError, ValueError):
            timestamp = datetime.now(timezone.utc) # Fallback, not ideal

        return EquityQuote(
            symbol=data.get("symbol", symbol_override or "UNKNOWN"),
            exchange=data.get("exchange"),
            price=data["close"],  # For EOD, 'close' is the latest price of that day
            change=data.get("adj_close", data["close"]) - data.get("adj_open", data["open"]), # Approximation
            percentChange=((data.get("adj_close", data["close"]) - data.get("adj_open", data["open"])) / data.get("adj_open", data["open"])) * 100 if data.get("adj_open") else 0, # Approximation
            previousClose=data.get("adj_open"), # This is an approximation, MarketStack EOD might not provide previous day's close directly
            open=data["open"],
            high=data["high"],
            low=data["low"],
            volume=int(data["volume"]) if data["volume"] is not None else None,
            timestamp=timestamp,
            # MarketStack EOD doesn't typically provide marketCap, yearHigh/Low, avgVolume directly in EOD results
            # These would require different endpoints or calculations.
            # Trading status would also require more info or a different endpoint for live status
        )

    async def get_equity_quote(self, symbol: str, exchange: Optional[str] = None) -> Optional[EquityQuote]:
        """
        Fetches the latest available EOD data as a quote from MarketStack.
        For true real-time, MarketStack might have different endpoints (e.g., intraday)
        but this uses /eod with a limit of 1 for simplicity for now.
        Alternatively, /tickers/{symbol}/eod/latest is available on some plans.
        Let's use the /eod endpoint with limit=1 for broader compatibility.
        """
        params = {"symbols": symbol, "limit": 1}
        if exchange: # MarketStack allows filtering by exchange with symbol, e.g. AAPL.XNAS
            params["symbols"] = f"{symbol}.{exchange}"
            
        try:
            data = await self._request(endpoint="/eod", params=params)
            if data and "data" in data and data["data"]:
                # Take the first item as it's the latest EOD quote
                quote_data = data["data"][0]
                return self._map_to_equity_quote(quote_data, symbol_override=symbol)
            return None
        except MarketDataError as e:
            # Log the error or handle it as needed, e.g. by re-raising or returning None
            print(f"MarketStack get_equity_quote error for {symbol}: {e.message}") # Replace with proper logging
            return None # Or re-raise if you want service layer to handle all None returns uniformly

    async def get_historical_price_data(
        self,
        symbol: str,
        from_date: date,
        to_date: date,
        exchange: Optional[str] = None
    ) -> List[HistoricalPricePoint]:
        params = {
            "symbols": symbol,
            "date_from": from_date.isoformat(),
            "date_to": to_date.isoformat(),
            "sort": "ASC" # Oldest to newest
        }
        if exchange:
             params["symbols"] = f"{symbol}.{exchange}"

        try:
            data = await self._request(endpoint="/eod", params=params)
            if data and "data" in data:
                return [self._map_to_historical_price_point(item) for item in data["data"]]
            return []
        except MarketDataError as e:
            print(f"MarketStack get_historical_price_data error for {symbol}: {e.message}") # Replace with proper logging
            return [] # Or re-raise


    async def get_company_profile(
        self,
        symbol: str,
        exchange: Optional[str] = None
    ) -> Optional[CompanyProfile]:
        # MarketStack's /tickers endpoint provides company info
        # /tickers/{symbol} for specific one
        # This might require a different plan level for full details.
        # For now, returning a placeholder.
        # Example: http://api.marketstack.com/v1/tickers/aapl?access_key=YOUR_ACCESS_KEY
        endpoint = f"/tickers/{symbol}"
        try:
            data = await self._request(endpoint=endpoint) # No additional params beyond API key
            if data: # Assuming 'data' is the direct object for a single ticker request
                # Mapping MarketStack ticker data to CompanyProfile
                # MarketStack fields for company profile: name, symbol, country, exchange, currency, has_intraday, has_eod etc.
                # It does not provide extensive descriptions, ceo, employees, logoUrl directly in this endpoint.
                # This would likely be supplemented by another provider like AlphaVantage if needed.
                return CompanyProfile(
                    symbol=data.get("symbol", symbol),
                    companyName=data.get("name", "N/A"),
                    exchange=data.get("exchange"), # Stock exchange name
                    country=data.get("country"),
                    currency=data.get("currency"), # From ticker_eod object if available
                    # Fields like description, industry, sector, website, logoUrl, ceo, employees
                    # are not typically available in MarketStack's basic ticker info.
                )
            return None
        except MarketDataError as e:
            print(f"MarketStack get_company_profile error for {symbol}: {e.message}")
            return None
        except Exception as e: # Catch unexpected structure
            print(f"Unexpected error mapping company profile for {symbol}: {str(e)}")
            return None


    async def get_news_articles(
        self,
        symbols: Optional[List[str]] = None,
        topics: Optional[List[str]] = None, # Marketstack uses 'sources' (e.g. -CNBC), not generic topics
        limit: int = 20,
        source: Optional[str] = None # Marketstack specific source filter
    ) -> List[NewsArticle]:
        # MarketStack /news endpoint
        # http://api.marketstack.com/v1/news?access_key=YOUR_ACCESS_KEY
        # &sources=cnn,-reuters&symbols=AAPL
        params = {"limit": str(limit)}
        if symbols:
            params["symbols"] = ",".join(symbols)
        if source: # For MarketStack, 'source' is often a news outlet like 'CNBC', 'Reuters'
             params["sources"] = source # Or multiple comma-separated: "cnn,-foxbusiness"
        
        # Note: MarketStack's 'topics' or 'keywords' filtering might be different or limited.
        # Their primary filter is 'sources' and 'symbols'.
        
        try:
            data = await self._request(endpoint="/news", params=params)
            news_list: List[NewsArticle] = []
            if data and "data" in data:
                for item in data["data"]:
                    # Mapping MarketStack news item to NewsArticle
                    news_list.append(NewsArticle(
                        id=item.get("url"), # MarketStack may not have a unique ID, use URL
                        headline=item["title"],
                        summary=item.get("description"),
                        source=item["source"],
                        url=item["url"],
                        publishedAt=datetime.fromisoformat(item["published_at"].replace("+0000", "+00:00")),
                        imageUrl=item.get("image"),
                        symbols=item.get("symbols", []), # MarketStack news items contain a list of symbols
                        # topics and sentiment might not be directly provided by MarketStack
                    ))
            return news_list
        except MarketDataError as e:
            print(f"MarketStack get_news_articles error: {e.message}")
            return []
        except Exception as e:
            print(f"Unexpected error mapping news for {str(e)}")
            return []


    # --- Placeholder implementations for other methods ---
    async def get_dividend_data(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        exchange: Optional[str] = None
    ) -> List[DividendData]:
        # MarketStack /dividends endpoint
        # http://api.marketstack.com/v1/dividends?access_key=YOUR_ACCESS_KEY&symbols=AAPL
        params: Dict[str, Any] = {"symbols": symbol}
        if from_date:
            params["date_from"] = from_date.isoformat()
        if to_date:
            params["date_to"] = to_date.isoformat()
        
        try:
            data = await self._request(endpoint="/dividends", params=params)
            dividend_list: List[DividendData] = []
            if data and "data" in data:
                for item in data["data"]:
                    # MarketStack dividend data: date, dividend, symbol
                    # We need to map this to our DividendData model
                    # 'date' is the payment date by MarketStack. Ex-dividend date might not be present here.
                    payment_dt = datetime.fromisoformat(item["date"].replace("+0000", "+00:00")).date()
                    
                    dividend_list.append(DividendData(
                        symbol=item["symbol"],
                        paymentDate=payment_dt, 
                        amount=item["dividend"],
                        # exDividendDate, recordDate, frequency, yield_value might need
                        # to come from another source or calculation if not directly provided.
                    ))
            return dividend_list
        except MarketDataError as e:
            print(f"MarketStack get_dividend_data error for {symbol}: {e.message}")
            return []
        except Exception as e:
            print(f"Unexpected error mapping dividends for {symbol}: {str(e)}")
            return []


    async def get_option_quote(self, contract_symbol: str) -> Optional[OptionQuote]:
        print(f"MarketStackAdapter: get_option_quote for {contract_symbol} - Not yet implemented for MarketStack or may require specific plan.")
        # MarketStack might have limited options data depending on plan.
        # This would typically involve a different endpoint.
        return None

    async def get_forex_quote(self, base_currency: str, quote_currency: str) -> Optional[ForexQuote]:
        print(f"MarketStackAdapter: get_forex_quote for {base_currency}/{quote_currency} - Not implemented or may use /currenices endpoint.")
        # MarketStack has a /currencies endpoint for Forex.
        # e.g. http://api.marketstack.com/v1/currencies/EURUSD?access_key=YOUR_ACCESS_KEY
        return None

    async def get_crypto_quote(self, base_asset: str, quote_asset: str) -> Optional[CryptoQuote]:
        print(f"MarketStackAdapter: get_crypto_quote for {base_asset}/{quote_asset} - MarketStack may have limited crypto data.")
        # MarketStack might not be the primary source for extensive crypto data.
        return None

    async def get_index_quote(self, symbol: str, exchange: Optional[str] = None) -> Optional[IndexQuote]:
        # MarketStack /indices endpoint. For example, INDX for S&P 500
        # http://api.marketstack.com/v1/tickers/INDX?access_key=YOUR_ACCESS_KEY (if INDX is an official symbol)
        # Or general EOD if it's treated like a stock: http://api.marketstack.com/v1/eod?access_key=YOUR_ACCESS_KEY&symbols=INDX
        # Let's try using the /eod endpoint as indices are often fetched like stocks.
        params = {"symbols": symbol, "limit": 1}
        if exchange:
             params["symbols"] = f"{symbol}.{exchange}" # Or however MarketStack handles index exchanges
        try:
            data = await self._request(endpoint="/eod", params=params) # Using /eod for indices
            if data and "data" in data and data["data"]:
                index_data = data["data"][0]
                # Map to IndexQuote. Many fields will be similar to EquityQuote
                timestamp = datetime.fromisoformat(index_data["date"].replace("+0000", "+00:00"))
                return IndexQuote(
                    symbol=index_data.get("symbol", symbol),
                    name=index_data.get("symbol", symbol), # MarketStack EOD won't provide a descriptive name, just symbol
                    price=index_data["close"],
                    change=index_data["close"] - index_data["open"], # Approximation
                    percentChange=((index_data["close"] - index_data["open"]) / index_data["open"]) * 100 if index_data["open"] else 0,
                    previousClose=index_data.get("open"), # Approximation
                    open=index_data["open"],
                    high=index_data["high"],
                    low=index_data["low"],
                    timestamp=timestamp,
                    exchange=index_data.get("exchange")
                )
            return None
        except MarketDataError as e:
            print(f"MarketStack get_index_quote error for {symbol}: {e.message}")
            return None
        except Exception as e:
            print(f"Unexpected error mapping index quote for {symbol}: {str(e)}")
            return None

    async def get_market_movers(
        self,
        market_segment: str, # e.g., 'gainers', 'losers', 'most_active'
        top_n: int = 10,
        exchange: Optional[str] = None
    ) -> List[MarketMover]:
        print(f"MarketStackAdapter: get_market_movers for {market_segment} - Not directly supported by standard MarketStack endpoints. This often requires premium data or specific provider features.")
        # MarketStack doesn't have a direct "market movers" endpoint in its basic API.
        # This functionality usually comes from more specialized financial data providers or requires manual calculation.
        return []

    async def search_symbols(self, query: str, asset_type: Optional[MarketAssetType] = None, limit: int = 10) -> List[CompanyProfile]:
        # MarketStack /tickers endpoint can be used for search with the 'search' parameter
        # http://api.marketstack.com/v1/tickers?access_key=YOUR_ACCESS_KEY&search=Apple
        params = {"search": query, "limit": str(limit)}
        # MarketStack doesn't directly filter by MarketAssetType in its symbol search in a structured way.
        # It might return various types.
        
        try:
            data = await self._request(endpoint="/tickers", params=params)
            profiles: List[CompanyProfile] = []
            if data and "data" in data:
                for item in data["data"]:
                    profiles.append(CompanyProfile(
                        symbol=item["symbol"],
                        companyName=item.get("name", "N/A"),
                        exchange=item.get("stock_exchange", {}).get("acronym") or item.get("exchange"), # stock_exchange.acronym is better if available
                        country=item.get("country"),
                        assetType= MarketAssetType.STOCK if item.get("has_eod") else MarketAssetType.OTHER # Basic inference
                        # Again, MarketStack /tickers is limited for full profile data.
                    ))
            return profiles
        except MarketDataError as e:
            print(f"MarketStack search_symbols error for '{query}': {e.message}")
            return []
        except Exception as e:
            print(f"Unexpected error mapping search results for '{query}': {str(e)}")
            return []

    async def close(self):
        """Closes the HTTP client session."""
        await self.client.aclose()
