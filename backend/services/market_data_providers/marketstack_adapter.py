# backend/services/market_data_providers/marketstack_adapter.py
import httpx
import os
import logging # Import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timezone
from backend.services.market_data_interface import MarketDataServiceInterface
from backend.schemas.market_data import (
    EquityQuote,
    HistoricalPricePoint,
    CompanyProfile,
    NewsArticle,
    DividendData,
    StockSplitData, # Added
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
             # This case should be handled or logged more gracefully, 
             # possibly by filtering out such records or raising an error.
            logger.error(f"Historical data point for symbol {item.get('symbol')} has invalid date: {item.get('date')}. Skipping.")
            # Depending on strictness, you might raise an error or return a sentinel value
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
        exchange_mic = item.get("exchange") # Marketstack EOD provides MIC in 'exchange' field

        # Basic change calculation from EOD data, might not be previous day's close
        change = item.get("adj_close", item["close"]) - item.get("adj_open", item["open"]) if item.get("adj_open") is not None and item.get("adj_close") is not None else 0
        percent_change = (change / item["adj_open"]) * 100 if item.get("adj_open") and item["adj_open"] != 0 else 0

        return EquityQuote(
            symbol=symbol,
            name=item.get("name"),
            exchangeSymbol=item.get("exchange_code"), # From EOD example: "NASDAQ"
            exchangeShortName=exchange_mic, # MIC e.g. XNAS
            assetType=MarketAssetType(item["asset_type"].upper()) if item.get("asset_type") else MarketAssetType.STOCK,
            country=None, # Not directly in EOD item, would be from profile
            currency=item.get("price_currency"),
            price=item["close"], 
            change=change,
            percentChange=percent_change,
            previousClose=item.get("adj_open"), # EOD 'open' or 'adj_open' as a proxy for prev close in some contexts
            open=item["open"],
            high=item["high"],
            low=item["low"],
            volume=int(item["volume"]) if item.get("volume") is not None else None,
            timestamp=timestamp,
            marketCap=None, 
            yearHigh=None, 
            yearLow=None,
            averageVolume=None,
            tradingStatus=None, # EOD is implicitly 'CLOSED' for the date given, but this field is for live status
            eps=None, peRatio=None, beta=None, fiftyTwoWeekHigh=None, fiftyTwoWeekLow=None, priceAvg50=None, priceAvg200=None, sharesOutstanding=None, earningDate=None,
            dividend_eod=item.get("dividend"), # Added
            split_factor_eod=item.get("split_factor") # Added
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
        profile = CompanyProfile(
            symbol=item["ticker"],
            name=item.get("name"),
            exchangeSymbol=item.get("exchange_code"), 
            assetType=MarketAssetType.STOCK, 
            country=addr.get("stateOrCountry") if addr.get("stateOrCountry") and len(addr.get("stateOrCountry")) == 2 else None,
            currency=item.get("reporting_currency"),
            shortName=item.get("name"), 
            longDescription=item.get("about"),
            industry=item.get("industry"),
            sector=item.get("sector"),
            website=item.get("website"),
            fullTimeEmployees=int(item["full_time_employees"]) if item.get("full_time_employees") else None,
            ipoDate=self._parse_iso_datetime(item.get("ipo_date")).isoformat() if self._parse_iso_datetime(item.get("ipo_date")) else None,
            foundedYear=int(self._parse_iso_datetime(item.get("date_founded")).year) if self._parse_iso_datetime(item.get("date_founded")) else None,
            address=f'{addr.get("street1", "")} {addr.get("street2", "")}'.strip(),
            city=addr.get("city"),
            state=addr.get("stateOrCountry") if addr.get("stateOrCountry") and len(addr.get("stateOrCountry")) == 2 else None,
            zipCode=addr.get("postal_code"),
            phoneNumber=item.get("phone"),
            isin=None, 
            cusip=None,
            cik=None, 
            lei=None, # Placeholder for lei
            sicCode=None, # Placeholder for sicCode
            sicName=None # Placeholder for sicName
        )
        logger.debug(f"Mapped company profile for {item.get('ticker')}")
        return profile

    async def get_company_profile(self, symbol: str, exchange: Optional[str] = None) -> Optional[CompanyProfile]:
        params = {"ticker": symbol}
        logger.info(f"Fetching company profile for {symbol} from MarketStack v2 using /tickerinfo")
        try:
            data = await self._request(endpoint="/tickerinfo", params=params)
            if data and "data" in data and isinstance(data["data"], dict):
                ticker_details_data = None
                try:
                    ticker_endpoint = f"/tickers/{symbol}"
                    if exchange: 
                        ticker_endpoint = f"/tickers/{symbol}.{exchange}"
                    ticker_details_data = await self._request(endpoint=ticker_endpoint)
                except MarketDataError as mde_ticker:
                    logger.warning(f"Could not fetch supplementary details from /tickers/{symbol} for profile: {mde_ticker.message}")

                profile = self._map_ticker_info_to_company_profile(data["data"])
                
                if ticker_details_data: # Merge data from /tickers/{symbol}
                    profile.cik = ticker_details_data.get("cik")
                    profile.isin = ticker_details_data.get("isin")
                    profile.cusip = ticker_details_data.get("cusip")
                    profile.exchangeSymbol = ticker_details_data.get("stock_exchange", {}).get("acronym", profile.exchangeSymbol)
                    profile.exchangeShortName = ticker_details_data.get("stock_exchange", {}).get("mic", profile.exchangeShortName)
                    profile.country = ticker_details_data.get("stock_exchange",{}).get("country_code",profile.country)
                    profile.sicCode = ticker_details_data.get("sic_code")
                    profile.sicName = ticker_details_data.get("sic_description") # Added sicName mapping
                    profile.lei = ticker_details_data.get("lei") # Added LEI mapping

                return profile
            logger.warning(f"No profile data found in response for {symbol} from /tickerinfo. Response: {data}")
            return None
        except MarketDataError as e:
            logger.error(f"MarketStack get_company_profile error for {symbol}: {e.message}")
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
            amount=float(item["dividend"]),
            exDividendDate=self._parse_iso_datetime(item.get("date")).isoformat() if self._parse_iso_datetime(item.get("date")) else None,
            paymentDate=self._parse_iso_datetime(item.get("payment_date")).isoformat() if self._parse_iso_datetime(item.get("payment_date")) else None,
            recordDate=self._parse_iso_datetime(item.get("record_date")).isoformat() if self._parse_iso_datetime(item.get("record_date")) else None,
            declaredDate=self._parse_iso_datetime(item.get("declaration_date")).isoformat() if self._parse_iso_datetime(item.get("declaration_date")) else None,
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
            logger.error(f"MarketStack get_dividend_data error for {symbol}: {e.message}")
            return []

    def _map_split_item(self, item: Dict[str, Any]) -> StockSplitData:
        return StockSplitData(
            symbol=item["symbol"],
            date=self._parse_iso_datetime(item.get("date")).isoformat() if self._parse_iso_datetime(item.get("date")) else "",
            split_factor=float(item["split_factor"]),
            stock_split_ratio=item.get("stock_split", "N/A")
        )

    async def get_stock_splits(
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
            logger.error(f"MarketStack get_stock_splits error for {symbol}: {e.message}")
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
                return IndexQuote(
                    symbol=index_data["benchmark"], 
                    name=index_data["benchmark"],
                    exchangeSymbol=None, 
                    price=float(index_data["price"]),
                    change=float(index_data["price_change_day"]),
                    percentChange=float(index_data["percentage_day"].rstrip('%')),
                    timestamp=self._parse_iso_datetime(index_data.get("date")) or datetime.now(timezone.utc),
                    country=index_data.get("country")
                )
            logger.warning(f"No data returned for index {symbol} from /indexinfo")
            return None
        except MarketDataError as e:
            logger.error(f"MarketStack get_index_quote error for {symbol}: {e.message}")
            return None
        except (ValueError, TypeError) as e:
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
                    stock_ex = item.get("stock_exchange", {})
                    profiles.append(CompanyProfile(
                        symbol=item["ticker"],
                        name=item.get("name"),
                        exchangeSymbol=stock_ex.get("acronym"),
                        exchangeShortName=stock_ex.get("mic"),
                        assetType=MarketAssetType.STOCK if item.get("has_eod") or item.get("has_intraday") else MarketAssetType.OTHER,
                    ))
            return profiles
        except MarketDataError as e:
            logger.error(f"MarketStack search_symbols error for '{query}': {e.message}")
            return []

    async def close(self):
        await self.client.aclose()
        logger.info("MarketStackAdapter HTTP client closed.")
