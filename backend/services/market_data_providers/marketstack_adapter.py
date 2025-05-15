import os
from datetime import date, datetime
from typing import Dict, List, Optional, Any, cast

import httpx
from fastapi import HTTPException

from backend.schemas.market_data import (
    # Phase 1 detailed schemas
    EquityQuote,
    HistoricalPricePoint,
    IntradayPricePoint,
    CompanyProfile,
    StockExchangeInfo,
    CompanyAddress,
    KeyExecutive,
    DividendData,
    StockSplitData,
    MarketAssetType,
    OptionQuote,
    ForexQuote,
    CryptoQuote,
    IndexQuote,
    MarketMover,
    # Phase 2 additions
    CommodityPrice,
    HistoricalCommodityPriceData,
    CommodityPricePoint,
    CommodityBasics,
    CompanyRatingData,
    CompanyRatingResult,
    CompanyBasics,
    CompanyRatingOutput,
    AnalystConsensus,
    AnalystRatingDetail,
    IndexBasicInfo,
    BondCountry,
    BondInfoData,
    ETFTicker,
    ETFHoldingDetails,
    ETFBasics,
    ETFOutput,
    ETFAttributes,
    ETFSignature,
    SectorWeight,
    ETFHolding
)
from backend.services.market_data_interface import MarketDataServiceInterface


class MarketStackAdapter(MarketDataServiceInterface):
    """Adapter for MarketStack API V2"""

    def __init__(self):
        self.api_key = os.environ.get("MARKETSTACK_API_KEY")
        if not self.api_key:
            raise ValueError("MARKETSTACK_API_KEY environment variable not set")
        
        self.base_url = "https://api.marketstack.com/v2"
        self.client = httpx.AsyncClient(timeout=30.0)  # 30 second timeout

    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict:
        """Make a request to the MarketStack API"""
        if params is None:
            params = {}
        
        # Add API key to params
        params["access_key"] = self.api_key
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise HTTPException(
                    status_code=429, 
                    detail="Rate limit exceeded for market data provider"
                )
            elif e.response.status_code == 401:
                raise HTTPException(
                    status_code=401, 
                    detail="Unauthorized access to market data provider"
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Market data provider error: {e.response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Market data provider request failed: {str(e)}"
            )


    async def get_index_quote(self, symbol: str) -> Optional[IndexQuote]:
        """Get current quote for a market index"""
        try:
            response = await self._make_request(
                "/indexinfo", {"benchmark": symbol}
            )
            
            if response.get("status") != "ok" or not response.get("result"):
                return None
            
            result = response["result"]
            
            return IndexQuote(
                symbol=symbol,
                name=result.get("basics", {}).get("name", "Unknown"),
                price=float(result.get("last", 0)),
                change=float(result.get("change_dollar", 0)),
                percent_change=float(result.get("change_percent", 0)),
                timestamp=datetime.fromisoformat(result.get("date", "").replace("Z", "+00:00"))
            )
        except Exception as e:
            print(f"Error fetching index quote: {e}")
            return None


    # Phase 2 - Commodity Prices
    async def get_commodity_price(self, commodity_name: str) -> Optional[CommodityPrice]:
        """Get current commodity price"""
        try:
            response = await self._make_request(
                "/commodities", {"commodity_name": commodity_name}
            )
            
            if response.get("status") != "ok" or not response.get("result"):
                return None
            
            result = response["result"]
            basics = result.get("basics", {})
            
            return CommodityPrice(
                commodity_name=basics.get("commodity_name", commodity_name),
                commodity_unit=basics.get("commodity_unit", ""),
                commodity_price=float(result.get("commodity_price", 0)),
                price_change_day=float(result.get("price_change_day", 0)),
                percentage_day=float(result.get("percentage_day", 0)),
                percentage_week=float(result.get("percentage_week", 0)),
                percentage_month=float(result.get("percentage_month", 0)),
                percentage_year=float(result.get("percentage_year", 0)),
                quarter1_25=float(result.get("quarter1_25", 0)),
                quarter2_25=float(result.get("quarter2_25", 0)),
                quarter3_25=float(result.get("quarter3_25", 0)),
                quarter4_25=float(result.get("quarter4_25", 0)),
                quarter1_24=float(result.get("quarter1_24", 0)),
                quarter2_24=float(result.get("quarter2_24", 0)),
                quarter3_24=float(result.get("quarter3_24", 0)),
                quarter4_24=float(result.get("quarter4_24", 0)),
                quarter1_23=float(result.get("quarter1_23", 0)),
                quarter2_23=float(result.get("quarter2_23", 0)),
                quarter3_23=float(result.get("quarter3_23", 0)),
                quarter4_23=float(result.get("quarter4_23", 0)),
                datetime=datetime.fromisoformat(result.get("datetime", "").replace("Z", "+00:00"))
            )
        except Exception as e:
            print(f"Error fetching commodity price: {e}")
            return None

    # Phase 2 - Historical Commodity Prices
    async def get_historical_commodity_prices(
        self, 
        commodity_name: str, 
        date_from: Optional[date] = None, 
        date_to: Optional[date] = None, 
        frequency: Optional[str] = None
    ) -> Optional[HistoricalCommodityPriceData]:
        """Get historical commodity prices"""
        params = {"commodity_name": commodity_name}
        
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        if frequency:
            params["frequency"] = frequency
        
        try:
            response = await self._make_request("/commoditieshistory", params)
            
            if response.get("status") != "ok" or not response.get("result"):
                return None
            
            result = response["result"]
            basics = result.get("basics", {})
            
            data_points = []
            for point in result.get("data", []):
                data_points.append(
                    CommodityPricePoint(
                        commodity_price=float(point.get("commodity_price", 0)),
                        date=datetime.fromisoformat(point.get("date", "").replace("Z", "+00:00"))
                    )
                )
            
            return HistoricalCommodityPriceData(
                basics=CommodityBasics(
                    commodity_name=basics.get("commodity_name", commodity_name),
                    commodity_unit=basics.get("commodity_unit", "")
                ),
                data=data_points
            )
        except Exception as e:
            print(f"Error fetching historical commodity prices: {e}")
            return None

    # Phase 2 - Company Ratings
    async def get_company_ratings(
        self, 
        ticker: str, 
        date_from: Optional[date] = None, 
        date_to: Optional[date] = None, 
        rated: Optional[str] = None
    ) -> Optional[CompanyRatingData]:
        """Get company analyst ratings"""
        params = {"ticker": ticker}
        
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        if rated:
            params["rated"] = rated
        
        try:
            response = await self._make_request("/companyratings", params)
            
            if response.get("status") != "ok" or not response.get("result"):
                return None
            
            result = response["result"]
            basics = result.get("basics", {})
            output = result.get("output", {})
            consensus = output.get("analyst_consensus", {})
            analysts_data = output.get("analysts", [])
            
            analysts = []
            for analyst in analysts_data:
                analysts.append(
                    AnalystRatingDetail(
                        analyst_name=analyst.get("analyst_name", ""),
                        analyst_rating=analyst.get("analyst_rating", ""),
                        target_price=float(analyst.get("target_price", 0)),
                        rating_date=datetime.fromisoformat(analyst.get("rating_date", "").replace("Z", "+00:00"))
                    )
                )
            
            return CompanyRatingData(
                status=response.get("status", ""),
                result=CompanyRatingResult(
                    basics=CompanyBasics(
                        ticker=basics.get("ticker", ticker),
                        name=basics.get("name", ""),
                        exchange=basics.get("exchange", "")
                    ),
                    output=CompanyRatingOutput(
                        analyst_consensus=AnalystConsensus(
                            buy=int(consensus.get("buy", 0)),
                            hold=int(consensus.get("hold", 0)),
                            sell=int(consensus.get("sell", 0)),
                            average_rating=float(consensus.get("average_rating", 0)),
                            average_target_price=float(consensus.get("average_target_price", 0)),
                            high_target_price=float(consensus.get("high_target_price", 0)),
                            low_target_price=float(consensus.get("low_target_price", 0)),
                            median_target_price=float(consensus.get("median_target_price", 0))
                        ),
                        analysts=analysts
                    )
                )
            )
        except Exception as e:
            print(f"Error fetching company ratings: {e}")
            return None

    # Phase 2 - Stock Market Index Listing
    async def list_stock_market_indexes(self, limit: int = 100, offset: int = 0) -> List[IndexBasicInfo]:
        """Get a list of all available stock market indexes/benchmarks"""
        params = {"limit": limit, "offset": offset}
        
        try:
            response = await self._make_request("/benchmarks", params)
            
            if response.get("status") != "ok" or not response.get("result"):
                return []
            
            result = response["result"]
            indexes = []
            
            for index_data in result:
                indexes.append(
                    IndexBasicInfo(
                        benchmark=index_data.get("benchmark", ""),
                        name=index_data.get("name", ""),
                        country=index_data.get("country", ""),
                        currency=index_data.get("currency", "")
                    )
                )
            
            return indexes
        except Exception as e:
            print(f"Error fetching stock market indexes: {e}")
            return []

    # Phase 2 - Bonds Data
    async def list_bond_countries(self, limit: int = 100, offset: int = 0) -> List[BondCountry]:
        """Get a list of bond-issuing countries"""
        params = {"limit": limit, "offset": offset}
        
        try:
            response = await self._make_request("/bondslist", params)
            
            if response.get("status") != "ok" or not response.get("result"):
                return []
            
            result = response["result"]
            countries = []
            
            for country_data in result:
                countries.append(
                    BondCountry(
                        country=country_data.get("country", "")
                    )
                )
            
            return countries
        except Exception as e:
            print(f"Error fetching bond countries: {e}")
            return []

    async def get_bond_info(self, country: str) -> Optional[BondInfoData]:
        """Get specific bond info for a country"""
        try:
            response = await self._make_request(
                "/bond", {"country": country}
            )
            
            if response.get("status") != "ok" or not response.get("result"):
                return None
            
            result = response["result"]
            
            return BondInfoData(
                region=result.get("region", ""),
                country=result.get("country", country),
                type=result.get("type", ""),
                yield_value=float(result.get("yield", 0)),
                price_change_day=float(result.get("price_change_day", 0)),
                percentage_week=float(result.get("percentage_week", 0)),
                percentage_month=float(result.get("percentage_month", 0)),
                percentage_year=float(result.get("percentage_year", 0)),
                datetime=datetime.fromisoformat(result.get("datetime", "").replace("Z", "+00:00"))
            )
        except Exception as e:
            print(f"Error fetching bond info: {e}")
            return None

    # Phase 2 - ETF Data
    async def list_etfs(self, limit: int = 100, offset: int = 0) -> List[ETFTicker]:
        """Get a list of ETFs"""
        params = {"list": "ticker", "limit": limit, "offset": offset}
        
        try:
            response = await self._make_request("/etflist", params)
            
            if response.get("status") != "ok" or not response.get("result"):
                return []
            
            result = response["result"]
            etfs = []
            
            for etf_data in result:
                etfs.append(
                    ETFTicker(
                        ticker=etf_data.get("ticker", "")
                    )
                )
            
            return etfs
        except Exception as e:
            print(f"Error fetching ETF list: {e}")
            return []

    async def get_etf_holdings(
        self, 
        ticker: str, 
        date_from: Optional[date] = None, 
        date_to: Optional[date] = None
    ) -> Optional[ETFHoldingDetails]:
        """Get detailed ETF holdings"""
        params = {"ticker": ticker}
        
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        
        try:
            response = await self._make_request("/etfholdings", params)
            
            if response.get("status") != "ok" or not response.get("result"):
                return None
            
            result = response["result"]
            basics = result.get("basics", {})
            output = result.get("output", {})
            attributes = output.get("attributes", {})
            signature = output.get("signature", {})
            holdings_data = output.get("holdings", [])
            
            # Process sector weights
            sector_weights = []
            for sector in signature.get("sector_weights", []):
                sector_weights.append(
                    SectorWeight(
                        sector=sector.get("sector", ""),
                        weight=float(sector.get("weight", 0))
                    )
                )
            
            # Process holdings
            holdings = []
            for holding in holdings_data:
                holdings.append(
                    ETFHolding(
                        ticker=holding.get("ticker", ""),
                        name=holding.get("name", ""),
                        weight=float(holding.get("weight", 0)),
                        shares=int(holding.get("shares", 0)),
                        market_value=float(holding.get("market_value", 0))
                    )
                )
            
            return ETFHoldingDetails(
                basics=ETFBasics(
                    ticker=basics.get("ticker", ticker),
                    name=basics.get("name", ""),
                    exchange=basics.get("exchange", "")
                ),
                output=ETFOutput(
                    attributes=ETFAttributes(
                        aum=float(attributes.get("aum", 0)),
                        expense_ratio=float(attributes.get("expense_ratio", 0)),
                        shares_outstanding=float(attributes.get("shares_outstanding", 0)),
                        nav=float(attributes.get("nav", 0))
                    ),
                    signature=ETFSignature(
                        sector_weights=sector_weights
                    ),
                    holdings=holdings
                )
            )
        except Exception as e:
            print(f"Error fetching ETF holdings: {e}")
            return None

    # Implement other required methods from MarketDataServiceInterface
    async def get_equity_quote(self, symbol: str, exchange: Optional[str] = None) -> Optional[EquityQuote]:
        """
        Get current equity quote for a symbol using the latest EOD data
        Uses MarketStack's /tickers/{symbol}/eod/latest or /eod endpoint
        """
        try:
            # Construct the endpoint and params
            endpoint = f"/tickers/{symbol}/eod/latest" if exchange is None else "/eod"
            params = {}
            
            if exchange:
                params["symbols"] = symbol
                params["exchange"] = exchange
            
            response = await self._make_request(endpoint, params)
            
            # Handle different response structures based on endpoint
            if endpoint.startswith("/tickers"):
                # Single result from /tickers/{symbol}/eod/latest
                if not response.get("data"):
                    return None
                
                data = response["data"]
                # If data is a list, take the first item
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
            else:
                # Multiple results from /eod
                if not response.get("data") or len(response["data"]) == 0:
                    return None
                
                # Take the most recent data point
                data = response["data"][0]
            
            # Calculate change and percent_change
            change = 0.0
            percent_change = 0.0
            
            # Map the response to EquityQuote schema
            return EquityQuote(
                symbol=symbol,
                name=data.get("name", "Unknown"),
                exchange=data.get("exchange", "Unknown"),
                price=float(data.get("adj_close", 0)),
                change=change,  # Would need previous day's close to calculate
                percent_change=percent_change,  # Would need previous day's close to calculate
                volume=int(data.get("volume", 0)),
                timestamp=datetime.fromisoformat(data.get("date", "").replace("Z", "+00:00")),
                open=float(data.get("open", 0)),
                high=float(data.get("high", 0)),
                low=float(data.get("low", 0)),
                adj_open=float(data.get("adj_open", 0)),
                adj_close=float(data.get("adj_close", 0)),
                dividend=float(data.get("dividend", 0)) if data.get("dividend") is not None else None,
                split_factor=float(data.get("split_factor", 1.0)) if data.get("split_factor") is not None else None,
                asset_type=data.get("asset_type", "Stock"),
                price_currency=data.get("price_currency", "USD").lower()
            )
        except Exception as e:
            print(f"Error fetching equity quote: {e}")
            return None

    async def get_historical_price_data(
        self,
        symbol: str,
        from_date: date,
        to_date: date,
        exchange: Optional[str] = None
    ) -> List[HistoricalPricePoint]:
        """
        Get historical price data for a symbol
        Uses MarketStack's /eod endpoint
        """
        params = {
            "symbols": symbol,
            "date_from": from_date.isoformat(),
            "date_to": to_date.isoformat(),
            "sort": "ASC"  # Sort by date ascending
        }
        
        if exchange:
            params["exchange"] = exchange
        
        try:
            response = await self._make_request("/eod", params)
            
            if not response.get("data"):
                return []
            
            historical_data = []
            for point in response["data"]:
                historical_data.append(
                    HistoricalPricePoint(
                        date=datetime.fromisoformat(point.get("date", "").replace("Z", "+00:00")),
                        open=float(point.get("open", 0)),
                        high=float(point.get("high", 0)),
                        low=float(point.get("low", 0)),
                        close=float(point.get("close", 0)),
                        volume=int(point.get("volume", 0)),
                        adj_high=float(point.get("adj_high", 0)),
                        adj_low=float(point.get("adj_low", 0)),
                        adj_open=float(point.get("adj_open", 0)),
                        adj_close=float(point.get("adj_close", 0)),
                        adj_volume=int(point.get("adj_volume", 0)),
                        split_factor=float(point.get("split_factor", 1.0)),
                        dividend=float(point.get("dividend", 0)),
                        symbol=symbol,
                        exchange=point.get("exchange", ""),
                        name=point.get("name", ""),
                        asset_type=point.get("asset_type", "Stock"),
                        price_currency=point.get("price_currency", "usd")
                    )
                )
            
            return historical_data
        except Exception as e:
            print(f"Error fetching historical price data: {e}")
            return []

    async def get_intraday_price_data(
        self,
        symbol: str,
        interval: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        exchange: Optional[str] = None
    ) -> List[IntradayPricePoint]:
        """
        Get intraday price data for a symbol
        Uses MarketStack's /intraday endpoint
        """
        params = {
            "symbols": symbol,
            "interval": interval
        }
        
        if exchange:
            params["exchange"] = exchange
        
        if from_date:
            params["date_from"] = from_date.isoformat()
        
        if to_date:
            params["date_to"] = to_date.isoformat()
        
        try:
            response = await self._make_request("/intraday", params)
            
            if not response.get("data"):
                return []
            
            intraday_data = []
            for point in response["data"]:
                intraday_data.append(
                    IntradayPricePoint(
                        date=datetime.fromisoformat(point.get("date", "").replace("Z", "+00:00")),
                        open=float(point.get("open", 0)),
                        high=float(point.get("high", 0)),
                        low=float(point.get("low", 0)),
                        close=float(point.get("close", 0)),
                        volume=float(point.get("volume", 0)),
                        symbol=symbol,
                        exchange=point.get("exchange", ""),
                        mid=float(point.get("mid")) if point.get("mid") is not None else None,
                        last_size=int(point.get("last_size")) if point.get("last_size") is not None else None,
                        bid_size=float(point.get("bid_size")) if point.get("bid_size") is not None else None,
                        bid_price=float(point.get("bid_price")) if point.get("bid_price") is not None else None,
                        ask_price=float(point.get("ask_price")) if point.get("ask_price") is not None else None,
                        ask_size=float(point.get("ask_size")) if point.get("ask_size") is not None else None,
                        last=float(point.get("last")) if point.get("last") is not None else None,
                        marketstack_last=float(point.get("marketstack_last")) if point.get("marketstack_last") is not None else None
                    )
                )
            
            return intraday_data
        except Exception as e:
            print(f"Error fetching intraday price data: {e}")
            return []

    async def get_company_profile(self, symbol: str, exchange: Optional[str] = None) -> Optional[CompanyProfile]:
        """
        Get company profile information
        Uses MarketStack's /tickerinfo and /tickers/{symbol} endpoints
        """
        try:
            # First, get basic ticker info
            ticker_params = {"ticker": symbol}
            ticker_info = await self._make_request("/tickerinfo", ticker_params)
            
            if not ticker_info.get("data"):
                return None
            
            ticker_data = ticker_info["data"]
            
            # Get additional ticker details if available
            additional_data = {}
            try:
                additional_response = await self._make_request(f"/tickers/{symbol}")
                if additional_response:
                    additional_data = additional_response
            except Exception as e:
                print(f"Error fetching additional ticker data: {e}")
            
            # Extract stock exchange info
            stock_exchange = None
            if ticker_data.get("stock_exchanges") and len(ticker_data["stock_exchanges"]) > 0:
                exchange_data = ticker_data["stock_exchanges"][0]
                stock_exchange = StockExchangeInfo(
                    name=exchange_data.get("exchange_name", ""),
                    acronym=exchange_data.get("acronym1", ""),
                    mic=exchange_data.get("exchange_mic", ""),
                    country=exchange_data.get("country", None),
                    country_code=exchange_data.get("alpha2_code", None),
                    city=exchange_data.get("city", None),
                    website=exchange_data.get("website", None)
                )
            else:
                # Create a minimal StockExchangeInfo if not available
                stock_exchange = StockExchangeInfo(
                    name="Unknown",
                    acronym="",
                    mic=""
                )
            
            # Extract address details
            address = None
            if ticker_data.get("address"):
                address_data = ticker_data["address"]
                address = CompanyAddress(
                    street1=address_data.get("street1", None),
                    street2=address_data.get("street2", None),
                    city=address_data.get("city", None),
                    postal_code=address_data.get("postal_code", None),
                    stateOrCountry=address_data.get("stateOrCountry", None),
                    state_or_country_description=address_data.get("state_or_country_description", None)
                )
            
            # Extract key executives
            key_executives = []
            if ticker_data.get("key_executives"):
                for exec_data in ticker_data["key_executives"]:
                    key_executives.append(
                        KeyExecutive(
                            name=exec_data.get("name", ""),
                            salary=exec_data.get("salary", None),
                            function=exec_data.get("function", None),
                            exercised=exec_data.get("exercised", None),
                            birth_year=exec_data.get("birth_year", None)
                        )
                    )
            
            # Create the CompanyProfile
            return CompanyProfile(
                symbol=symbol,
                name=ticker_data.get("name", ""),
                stock_exchange_info=stock_exchange,
                asset_type=ticker_data.get("item_type", "equity"),
                currency=additional_data.get("currency", None),
                about=ticker_data.get("about", None),
                industry=ticker_data.get("industry", None),
                sector=ticker_data.get("sector", None),
                website=ticker_data.get("website", None),
                full_time_employees=int(ticker_data.get("full_time_employees", 0)) if ticker_data.get("full_time_employees") else None,
                ipo_date=date.fromisoformat(ticker_data.get("ipo_date")) if ticker_data.get("ipo_date") else None,
                date_founded=date.fromisoformat(ticker_data.get("date_founded")) if ticker_data.get("date_founded") else None,
                address_details=address,
                phone_number=ticker_data.get("phone", None),
                key_executives=key_executives if key_executives else None,
                cik=additional_data.get("cik", None),
                isin=additional_data.get("isin", None),
                cusip=additional_data.get("cusip", None),
                ein=ticker_data.get("ein_employer_id", None),
                lei=additional_data.get("lei", None),
                sic_code=ticker_data.get("sic_code", None),
                sic_name=ticker_data.get("sic_name", None),
                item_type=ticker_data.get("item_type", None)
            )
        except Exception as e:
            print(f"Error fetching company profile: {e}")
            return None

    async def get_dividend_data(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        exchange: Optional[str] = None
    ) -> List[DividendData]:
        """
        Get dividend data for a symbol
        Uses MarketStack's /dividends endpoint
        """
        params = {"symbols": symbol}
        
        if exchange:
            params["exchange"] = exchange
        
        if from_date:
            params["date_from"] = from_date.isoformat()
        
        if to_date:
            params["date_to"] = to_date.isoformat()
        
        try:
            response = await self._make_request("/dividends", params)
            
            if not response.get("data"):
                return []
            
            dividend_data = []
            for div in response["data"]:
                dividend_data.append(
                    DividendData(
                        date=datetime.fromisoformat(div.get("date", "").replace("Z", "+00:00")),
                        dividend=float(div.get("dividend", 0)),
                        symbol=symbol,
                        payment_date=datetime.fromisoformat(div.get("payment_date", "").replace("Z", "+00:00")) if div.get("payment_date") else None,
                        record_date=datetime.fromisoformat(div.get("record_date", "").replace("Z", "+00:00")) if div.get("record_date") else None,
                        declaration_date=datetime.fromisoformat(div.get("declaration_date", "").replace("Z", "+00:00")) if div.get("declaration_date") else None,
                        distr_freq=div.get("distr_freq", None)
                    )
                )
            
            return dividend_data
        except Exception as e:
            print(f"Error fetching dividend data: {e}")
            return []

    async def get_stock_split_data(
        self,
        symbol: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        exchange: Optional[str] = None
    ) -> List[StockSplitData]:
        """
        Get stock split data for a symbol
        Uses MarketStack's /splits endpoint
        """
        params = {"symbols": symbol}
        
        if exchange:
            params["exchange"] = exchange
        
        if from_date:
            params["date_from"] = from_date.isoformat()
        
        if to_date:
            params["date_to"] = to_date.isoformat()
        
        try:
            response = await self._make_request("/splits", params)
            
            if not response.get("data"):
                return []
            
            split_data = []
            for split in response["data"]:
                split_data.append(
                    StockSplitData(
                        date=date.fromisoformat(split.get("date", "").split("T")[0]),
                        split_factor=float(split.get("split_factor", 1.0)),
                        symbol=symbol,
                        stock_split=split.get("stock_split", "")
                    )
                )
            
            return split_data
        except Exception as e:
            print(f"Error fetching stock split data: {e}")
            return []

    async def get_option_quote(self, contract_symbol: str) -> Optional[Any]:
        """Placeholder for get_option_quote method"""
        pass

    async def get_forex_quote(self, base_currency: str, quote_currency: str) -> Optional[ForexQuote]:
        """
        Get current forex exchange rate
        Uses MarketStack's /forex endpoint
        """
        try:
            response = await self._make_request(
                "/forex", {"base": base_currency, "quote": quote_currency}
            )
            
            if response.get("status") != "ok" or not response.get("result"):
                return None
            
            result = response["result"]
            
            return ForexQuote(
                base_currency=base_currency,
                quote_currency=quote_currency,
                rate=float(result.get("rate", 0)),
                timestamp=datetime.fromisoformat(result.get("date", "").replace("Z", "+00:00")),
                change=float(result.get("change", 0)) if result.get("change") is not None else None,
                percent_change=float(result.get("percent_change", 0)) if result.get("percent_change") is not None else None
            )
        except Exception as e:
            print(f"Error fetching forex quote: {e}")
            return None

    async def get_crypto_quote(self, base_asset: str, quote_asset: str) -> Optional[Any]:
        """Placeholder for get_crypto_quote method"""
        pass

    async def get_market_movers(self, market_segment: str, top_n: int = 10, exchange: Optional[str] = None) -> List[Any]:
        """Placeholder for get_market_movers method"""
        return []

    async def search_symbols(
        self,
        query: str,
        asset_type: Optional[MarketAssetType] = None,
        limit: int = 10
    ) -> List[CompanyProfile]:
        """
        Search for symbols based on a query string
        Uses MarketStack's /tickerslist endpoint
        """
        params = {
            "search": query,
            "limit": limit
        }
        
        try:
            response = await self._make_request("/tickerslist", params)
            
            if not response.get("data"):
                return []
            
            search_results = []
            for item in response["data"]:
                # Skip if asset_type filter is provided and doesn't match
                if asset_type and item.get("asset_type") != asset_type.value:
                    continue
                
                # Create a minimal StockExchangeInfo
                stock_exchange = StockExchangeInfo(
                    name=item.get("stock_exchange", {}).get("name", "Unknown"),
                    acronym=item.get("stock_exchange", {}).get("acronym", ""),
                    mic=item.get("stock_exchange", {}).get("mic", "")
                )
                
                # Create a minimal CompanyProfile for search results
                search_results.append(
                    CompanyProfile(
                        symbol=item.get("ticker", ""),
                        name=item.get("name", ""),
                        stock_exchange_info=stock_exchange,
                        asset_type=item.get("asset_type", "equity")
                    )
                )
            
            return search_results
        except Exception as e:
            print(f"Error searching symbols: {e}")
            return []
