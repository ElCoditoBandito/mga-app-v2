# backend/services/market_data_providers/marketstack_adapter.py
import httpx
import os
import logging # Import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timezone
from backend.services.market_data_interface import MarketDataServiceInterface
from backend.schemas.market_data import (
    CompanyAddress,
    StockExchangeInfo, # Added StockExchangeInfo
    EquityQuote,
    HistoricalPricePoint,
    CompanyProfile,
    NewsArticle,
    DividendData,
    StockSplitData, 
    OptionQuote,
    ForexQuote,
    CryptoQuote,
    IndexQuote,
    MarketMover,
    MarketAssetType,
    MarketTradingStatus,
    MarketDataError
)

logger = logging.getLogger(__name__) # Create a logger for this module

MARKET_STACK_API_KEY = os.getenv("MARKET_STACK_API_KEY")
MARKET_STACK_BASE_URL = "https://api.marketstack.com/v2" # Updated to v2

class MarketStackAdapter(MarketDataServiceInterface):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or MARKET_STACK_API_KEY
        if not self.api_key:
            logger.error("MarketStack API key is required but not found.")
            raise ValueError("MarketStack API key is required.")
        self.client = httpx.AsyncClient(base_url=MARKET_STACK_BASE_URL, timeout=10.0)
        logger.info(f"MarketStackAdapter initialized with base URL: {MARKET_STACK_BASE_URL}")

    async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        if not self.api_key:
            logger.error("MarketStack API key not configured at time of request.")
            raise MarketDataError(message="MarketStack API key not configured.", provider="MarketStack")

        all_params = params.copy() if params else {}
        all_params["access_key"] = self.api_key
        
        logger.debug(f"MarketStack request: Endpoint={endpoint}, Params={all_params.get('symbols') or all_params.get('ticker') or 'N/A'}")

        try:
            response = await self.client.get(endpoint, params=all_params)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as e:
            logger.warning(f"MarketStack request timed out for endpoint {endpoint}: {e}")
            raise MarketDataError(message=f"MarketStack request timed out: {e}", provider="MarketStack")
        except httpx.HTTPStatusError as e:
            error_details = "No specific error details from provider."
            error_code_from_provider = str(e.response.status_code)
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    err_obj = error_data["error"]
                    error_details = err_obj.get("message", error_details)
                    error_code_from_provider = err_obj.get("code", error_code_from_provider)
                    if "context" in err_obj:
                        error_details += f" Context: {err_obj['context']}"
            except Exception as parse_exc:
                logger.warning(f"Failed to parse MarketStack error response body: {parse_exc}")
            
            logger.warning(
                f"MarketStack API error: Status={e.response.status_code}, Code={error_code_from_provider}, Details={error_details} for endpoint {endpoint}"
            )
            raise MarketDataError(
                message=f"MarketStack API error: {e.response.status_code} - {error_details}",
                provider="MarketStack",
                errorCode=error_code_from_provider
            )
        except httpx.RequestError as e:
            logger.error(f"Error connecting to MarketStack for endpoint {endpoint}: {e}")
            raise MarketDataError(message=f"Error connecting to MarketStack: {e}", provider="MarketStack")
        except Exception as e:
            logger.exception(f"An unexpected error occurred with MarketStack for endpoint {endpoint}: {e}")
            raise MarketDataError(message=f"An unexpected error occurred with MarketStack: {str(e)}", provider="MarketStack")

    def _parse_iso_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            # Handles formats like "2024-09-27T00:00:00+0000" or "2024-08-15 04:00:00"
            # or "2025-03-24T15:42:00.000"
            if '+' in date_str and date_str.endswith("+0000"):
                date_str = date_str.replace("+0000", "+00:00")
            elif ' ' in date_str and ':' in date_str and '.' not in date_str and '+' not in date_str and 'Z' not in date_str.upper():
                # Attempt to make it more ISO compliant if it's like "YYYY-MM-DD HH:MM:SS"
                date_str = date_str.replace(" ", "T") + "Z" # Assume UTC if no offset
            return datetime.fromisoformat(date_str)
        except ValueError as ve:
            logger.warning(f"Could not parse date string '{date_str}': {ve}")
            try: # Fallback for simple YYYY-MM-DD if time parsing fails
                return datetime.combine(date.fromisoformat(date_str.split('T')[0]), datetime.min.time(), tzinfo=timezone.utc)
            except ValueError:
                 logger.error(f"Completely failed to parse date string '{date_str}'")
                 return None

    def _map_eod_item_to_historical_price_point(self, item: Dict[str, Any]) -> HistoricalPricePoint:
        dt_object = self._parse_iso_datetime(item.get("date"))
        if not dt_object:
            logger.error(f"Historical data point for symbol {item.get('symbol')} has invalid date: {item.get('date')}. Skipping.")
            raise ValueError(f"Invalid date in historical data: {item.get('date')}") 

        return HistoricalPricePoint(
            date=dt_object,
            open=item["open"],
            high=item["high"],
            low=item["low"],
            close=item["close"],
            adjustedClose=item.get("adj_close"),
            volume=int(item["volume"]) if item.get("volume") is not None else 0,
        )

    def _map_eod_item_to_equity_quote(self, item: Dict[str, Any], symbol_override: Optional[str] = None) -> EquityQuote:
        timestamp = self._parse_iso_datetime(item.get("date")) or datetime.now(timezone.utc)
        symbol = item.get("symbol", symbol_override or "UNKNOWN")
        
        stock_ex_info = StockExchangeInfo(
            mic=item.get("exchange") # Marketstack EOD provides MIC in 'exchange' field
        )
        # Marketstack EOD /tickers/{symbol}/eod/latest might not have 'exchange_code' or full stock_exchange details
        # So we prioritize MIC from the EOD item.

        change = item.get("adj_close", item["close"]) - item.get("adj_open", item["open"]) if item.get("adj_open") is not None and item.get("adj_close") is not None else 0
        percent_change = (change / item["adj_open"]) * 100 if item.get("adj_open") and item["adj_open"] != 0 else 0

        return EquityQuote(
            symbol=symbol,
            name=item.get("name"),
            stock_exchange_info=stock_ex_info,
            asset_type=MarketAssetType(item["asset_type"].upper()) if item.get("asset_type") else MarketAssetType.STOCK,
            currency=item.get("price_currency"),
            price=item["close"], 
            change=change,
            percentChange=percent_change,
            previousClose=item.get("adj_open"),
            open=item["open"],
            high=item["high"],
            low=item["low"],
            volume=int(item["volume"]) if item.get("volume") is not None else None,
            timestamp=timestamp,
            marketCap=None, 
            yearHigh=None, 
            yearLow=None,
            averageVolume=None,
            tradingStatus=None,
            eps=None, peRatio=None, beta=None, fiftyTwoWeekHigh=None, fiftyTwoWeekLow=None, priceAvg50=None, priceAvg200=None, sharesOutstanding=None, earningDate=None,
            dividend_eod=item.get("dividend"),
            split_factor_eod=item.get("split_factor")
        )

    async def get_equity_quote(self, symbol: str, exchange: Optional[str] = None) -> Optional[EquityQuote]:
        symbol_to_use = f"{symbol}.{exchange}" if exchange else symbol
        endpoint = f"/tickers/{symbol_to_use}/eod/latest"
        logger.info(f"Fetching latest EOD equity quote for {symbol_to_use} from MarketStack v2 using endpoint: {endpoint}")

        try:
            response_data = await self._request(endpoint=endpoint) 
            
            if response_data:
                quote_data_list = response_data.get("data", []) if isinstance(response_data, dict) and "data" in response_data else [response_data]
                if quote_data_list:
                    actual_quote_data = quote_data_list[0]
                    return self._map_eod_item_to_equity_quote(actual_quote_data, symbol_override=symbol)
                else:
                    logger.warning(f"No quote data found for {symbol_to_use} in MarketStack v2 response. Response: {response_data}")
                    return None
            logger.warning(f"Empty response for equity quote {symbol_to_use} from MarketStack v2.")
            return None
        except MarketDataError as e:
            logger.error(f"MarketStack get_equity_quote error for {symbol}: {e.message}")
            return None

    async def get_historical_price_data(
        self,
        symbol: str,
        from_date: date,
        to_date: date,
        exchange: Optional[str] = None
    ) -> List[HistoricalPricePoint]:
        symbol_to_use = f"{symbol}.{exchange}" if exchange else symbol
        params = {
            "symbols": symbol_to_use,
            "date_from": from_date.isoformat(),
            "date_to": to_date.isoformat(),
            "sort": "ASC"
        }
        endpoint = "/eod"
        logger.info(f"Fetching historical EOD for {symbol_to_use} from MarketStack v2 ({from_date} to {to_date})")
        try:
            data = await self._request(endpoint=endpoint, params=params)
            if data and "data" in data and data["data"]:
                return [self._map_eod_item_to_historical_price_point(item) for item in data["data"]]
            return []
        except MarketDataError as e:
            logger.error(f"MarketStack get_historical_price_data error for {symbol}: {e.message}")
            return []
        except ValueError as ve: # Catch date parsing errors from mapping
            logger.error(f"Error mapping historical price data for {symbol}: {ve}")
            return []

    def _map_ticker_info_to_company_profile(self, item: Dict[str, Any]) -> CompanyProfile:
        addr = item.get("address", {}) 
        fte_value = item.get("full_time_employees")
        fte_str: Optional[str] = str(fte_value) if fte_value is not None else None

        address_obj = None
        if isinstance(addr, dict):
            address_obj = CompanyAddress(
                street1=addr.get("street1"),
                street2=addr.get("street2"),
                city=addr.get("city"),
                state_or_country=addr.get("stateOrCountry"),
                postal_code=addr.get("postal_code"),
                state_or_country_description=addr.get("stateOrCountryDescription")
            )
        elif isinstance(addr, str):
            address_obj = CompanyAddress(street1=addr) 
            logger.warning(f"Address for {item.get('ticker')} was a string, mapped to street1: {addr}")
        
        # Initial stock_exchange_info from /tickerinfo data
        # /tickerinfo provides exchange_code directly, no sub-object for stock_exchange
        # It might also provide country directly (though typically from address.stateOrCountry if it's a country code)
        stock_ex_info = StockExchangeInfo(
            acronym=item.get("exchange_code"), # /tickerinfo has exchange_code
            # country_code from address.stateOrCountry if it's a 2-letter code, or from /tickers endpoint later
            country_code=addr.get("stateOrCountry") if isinstance(addr, dict) and addr.get("stateOrCountry") and len(addr.get("stateOrCountry")) == 2 else None,
            name=item.get("exchange_name") # If /tickerinfo provides a full exchange name
        )

        profile = CompanyProfile(
            symbol=item["ticker"],
            name=item.get("name"),
            stock_exchange_info=stock_ex_info,
            asset_type=MarketAssetType.STOCK, 
            currency=item.get("reporting_currency"),
            about=item.get("about"),
            industry=item.get("industry"),
            sector=item.get("sector"),
            website=item.get("website"), # Validator handles HttpUrl conversion
            full_time_employees=fte_str,
            ipo_date=self._parse_iso_datetime(item.get("ipo_date")).date() if self._parse_iso_datetime(item.get("ipo_date")) else None,
            date_founded=self._parse_iso_datetime(item.get("date_founded")).date() if self._parse_iso_datetime(item.get("date_founded")) else None,
            address_details=address_obj,
            phone_number=item.get("phone"),
            # These are typically from /tickers/{symbol} or other sources
            isin=None, 
            cusip=None,
            cik=None, 
            lei=None, 
            sic_code=None, 
            sic_name=None 
        )
        logger.debug(f"Mapped company profile for {item.get('ticker')} from /tickerinfo")
        return profile

    async def get_company_profile(self, symbol: str, exchange: Optional[str] = None) -> Optional[CompanyProfile]:
        params = {"ticker": symbol}
        logger.info(f"Fetching company profile for {symbol} from MarketStack v2 using /tickerinfo")
        try:
            data = await self._request(endpoint="/tickerinfo", params=params)
            if data and "data" in data and isinstance(data["data"], dict):
                ticker_info_data = data["data"]
                profile = self._map_ticker_info_to_company_profile(ticker_info_data)

                ticker_details_data = None
                try:
                    # The /tickers/{symbol} endpoint provides richer stock_exchange details
                    ticker_endpoint = f"/tickers/{symbol}"
                    # Note: Marketstack documentation for /tickers/{symbol} doesn't mention adding .EXCHANGE suffix for this specific endpoint
                    # but it's good to be consistent if other parts of their API use it for disambiguation.
                    # For now, assuming /tickers/{symbol} takes the plain symbol.
                    # If exchange-specific /tickers/ endpoint is needed, the logic would be: 
                    # if exchange: ticker_endpoint = f"/tickers/{symbol}.{exchange}"
                    ticker_details_data = await self._request(endpoint=ticker_endpoint) 
                except MarketDataError as mde_ticker:
                    logger.warning(f"Could not fetch supplementary details from /tickers/{symbol} for profile: {mde_ticker}")
                
                if ticker_details_data: # Merge data from /tickers/{symbol}
                    profile.cik = ticker_details_data.get("cik", profile.cik)
                    profile.isin = ticker_details_data.get("isin", profile.isin)
                    profile.cusip = ticker_details_data.get("cusip", profile.cusip)
                    profile.lei = ticker_details_data.get("lei", profile.lei)
                    profile.sic_code = ticker_details_data.get("sic_code", profile.sic_code)
                    profile.sic_name = ticker_details_data.get("sic_description", profile.sic_name)
                    
                    # Merge stock_exchange details from /tickers/{symbol} into profile.stock_exchange_info
                    if not profile.stock_exchange_info: # Ensure it exists
                        profile.stock_exchange_info = StockExchangeInfo()
                    
                    ms_stock_exchange = ticker_details_data.get("stock_exchange")
                    if isinstance(ms_stock_exchange, dict):
                        profile.stock_exchange_info.name = ms_stock_exchange.get("name", profile.stock_exchange_info.name)
                        profile.stock_exchange_info.acronym = ms_stock_exchange.get("acronym", profile.stock_exchange_info.acronym)
                        profile.stock_exchange_info.mic = ms_stock_exchange.get("mic", profile.stock_exchange_info.mic)
                        profile.stock_exchange_info.country = ms_stock_exchange.get("country", profile.stock_exchange_info.country)
                        profile.stock_exchange_info.country_code = ms_stock_exchange.get("country_code", profile.stock_exchange_info.country_code)
                        profile.stock_exchange_info.city = ms_stock_exchange.get("city", profile.stock_exchange_info.city)
                        # Marketstack uses 'website' for this, our model uses 'website_str' alias
                        profile.stock_exchange_info.website = ms_stock_exchange.get("website") 

                logger.debug(f"Final mapped company profile for {symbol}")
                return profile
            
            logger.warning(f"No profile data found in response for {symbol} from /tickerinfo. Response: {data}")
            return None
        except MarketDataError as e:
            logger.error(f"MarketStack get_company_profile error for {symbol}: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error in get_company_profile for {symbol}: {e}")
            return None

    async def get_news_articles(
        self,
        symbols: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        limit: int = 20,
        source: Optional[str] = None
    ) -> List[NewsArticle]:
        logger.warning("MarketStackAdapter (v2): The general /news endpoint is not listed in the provided v2 documentation. "
                       "This functionality might be deprecated or changed. Consider using a different provider for news.")
        return []

    def _map_dividend_item(self, item: Dict[str, Any]) -> DividendData:
        return DividendData(
            symbol=item["symbol"],
            dividend_amount=float(item["dividend"]),
            date=self._parse_iso_datetime(item.get("date")),
            payment_date=self._parse_iso_datetime(item.get("payment_date")),
            record_date=self._parse_iso_datetime(item.get("record_date")),
            declaration_date=self._parse_iso_datetime(item.get("declaration_date")),
            frequency=item.get("distr_freq")
        )

    async def get_dividend_data(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        exchange: Optional[str] = None 
    ) -> List[DividendData]:
        params: Dict[str, Any] = {"symbols": symbol}
        if from_date:
            params["date_from"] = from_date.isoformat()
        if to_date:
            params["date_to"] = to_date.isoformat()
        
        logger.info(f"Fetching dividend data for {symbol} from MarketStack v2")
        try:
            data = await self._request(endpoint="/dividends", params=params)
            if data and "data" in data and data["data"]:
                return [self._map_dividend_item(item) for item in data["data"]]
            return []
        except MarketDataError as e:
            logger.error(f"MarketStack get_dividend_data error for {symbol}: {e}")
            return []

    def _map_split_item(self, item: Dict[str, Any]) -> StockSplitData:
        return StockSplitData(
            symbol=item["symbol"],
            date=self._parse_iso_datetime(item.get("date")),
            split_factor=float(item["split_factor"]),
            stock_split_ratio=item.get("stock_split", "N/A")
        )

    async def get_stock_split_data(
        self, 
        symbol: str, 
        from_date: Optional[date] = None, 
        to_date: Optional[date] = None,
        exchange: Optional[str] = None
    ) -> List[StockSplitData]:
        params: Dict[str, Any] = {"symbols": symbol}
        if from_date:
            params["date_from"] = from_date.isoformat()
        if to_date:
            params["date_to"] = to_date.isoformat()

        logger.info(f"Fetching stock splits for {symbol} from MarketStack v2")
        try:
            data = await self._request(endpoint="/splits", params=params)
            if data and "data" in data and data["data"]:
                return [self._map_split_item(item) for item in data["data"]]
            return []
        except MarketDataError as e:
            logger.error(f"MarketStack get_stock_split_data error for {symbol}: {e}")
            return []

    async def get_option_quote(self, contract_symbol: str) -> Optional[OptionQuote]:
        logger.warning(f"MarketStackAdapter: get_option_quote for {contract_symbol} - MarketStack v2 does not seem to have a general options endpoint in provided docs.")
        return None

    async def get_forex_quote(self, base_currency: str, quote_currency: str) -> Optional[ForexQuote]:
        logger.warning(f"MarketStackAdapter: get_forex_quote for {base_currency}/{quote_currency} - V2 /currencies endpoint lists currencies, direct pair quote needs specific handling.")
        return None

    async def get_crypto_quote(self, base_asset: str, quote_asset: str) -> Optional[CryptoQuote]:
        logger.warning(f"MarketStackAdapter: get_crypto_quote for {base_asset}/{quote_asset} - MarketStack v2 crypto data availability and endpoints not specified in provided general docs.")
        return None

    async def get_index_quote(self, symbol: str, exchange: Optional[str] = None) -> Optional[IndexQuote]:
        params = {"index": symbol}
        logger.info(f"Fetching index quote for {symbol} from MarketStack v2 using /indexinfo")
        try:
            data = await self._request(endpoint="/indexinfo", params=params)
            if data and isinstance(data, list) and data:
                index_data = data[0]
                # IndexQuote model expects stock_exchange_info, but /indexinfo doesn't provide it directly.
                # We will pass None for now, or one could attempt to derive it if needed.
                return IndexQuote(
                    symbol=index_data["benchmark"], 
                    name=index_data["benchmark"],
                    stock_exchange_info=None, # Or map if possible
                    price=float(index_data["price"]),
                    change=float(index_data["price_change_day"]),
                    percentChange=float(index_data["percentage_day"].rstrip('%')),
                    timestamp=self._parse_iso_datetime(index_data.get("date")) or datetime.now(timezone.utc),
                    region=index_data.get("country") # /indexinfo uses 'country' for region
                )
            logger.warning(f"No data returned for index {symbol} from /indexinfo")
            return None
        except MarketDataError as e:
            logger.error(f"MarketStack get_index_quote error for {symbol}: {e}")
            return None
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Error mapping index data for {symbol}: {e}")
            return None

    async def get_market_movers(
        self,
        market_segment: str,
        top_n: int = 10,
        exchange: Optional[str] = None
    ) -> List[MarketMover]:
        logger.warning("MarketStackAdapter: get_market_movers - MarketStack v2 does not provide a direct market movers endpoint in the provided docs.")
        return []

    async def search_symbols(self, query: str, asset_type: Optional[MarketAssetType] = None, limit: int = 10) -> List[CompanyProfile]:
        params = {"search": query, "limit": str(limit)}
        logger.info(f"Searching symbols for '{query}' using MarketStack v2 /tickerslist")
        try:
            data = await self._request(endpoint="/tickerslist", params=params)
            profiles: List[CompanyProfile] = []
            if data and "data" in data:
                for item in data["data"]:
                    # /tickerslist provides stock_exchange object directly
                    ms_stock_exchange = item.get("stock_exchange", {})
                    stock_ex_info = StockExchangeInfo(
                        name=ms_stock_exchange.get("name"),
                        acronym=ms_stock_exchange.get("acronym"),
                        mic=ms_stock_exchange.get("mic"),
                        country=ms_stock_exchange.get("country"),
                        country_code=ms_stock_exchange.get("country_code")
                    )
                    profiles.append(CompanyProfile(
                        symbol=item["ticker"],
                        name=item.get("name"),
                        stock_exchange_info=stock_ex_info,
                        asset_type=MarketAssetType.STOCK if item.get("has_eod") or item.get("has_intraday") else MarketAssetType.OTHER,
                        # Other fields for CompanyProfile are not available in /tickerslist
                    ))
            return profiles
        except MarketDataError as e:
            logger.error(f"MarketStack search_symbols error for '{query}': {e}")
            return []

    async def close(self):
        await self.client.aclose()
        logger.info("MarketStackAdapter HTTP client closed.")
