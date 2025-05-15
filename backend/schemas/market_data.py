# backend/schemas/market_data.py
from typing import List, Optional, TypeVar, Generic, Dict, Any
from pydantic import BaseModel, HttpUrl, Field, validator
from datetime import date, datetime
from enum import Enum

class MarketAssetType(str, Enum):
    STOCK = "STOCK"
    ETF = "ETF"
    MUTUAL_FUND = "MUTUAL_FUND"
    OPTION = "OPTION"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    INDEX = "INDEX"
    BOND = "BOND"
    COMMODITY = "COMMODITY"
    OTHER = "OTHER"

class MarketTradingStatus(str, Enum):
    PRE_MARKET = "PRE_MARKET"
    REGULAR_MARKET = "REGULAR_MARKET"
    POST_MARKET = "POST_MARKET"
    EXTENDED_HOURS = "EXTENDED_HOURS"
    CLOSED = "CLOSED"
    HALTED = "HALTED"
    UNKNOWN = "UNKNOWN"

class StockExchangeInfo(BaseModel):
    name: Optional[str] = None
    acronym: Optional[str] = None
    mic: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = Field(None, alias="countryCode")
    city: Optional[str] = None
    website: Optional[HttpUrl] = Field(None, alias="website_str")
    operating_mic: Optional[str] = Field(None, alias="operatingMic")
    oprt_sgmt: Optional[str] = Field(None, alias="oprtSgmt")
    legal_entity_name: Optional[str] = Field(None, alias="legalEntityName")
    exchange_lei: Optional[str] = Field(None, alias="exchangeLei")
    market_category_code: Optional[str] = Field(None, alias="marketCategoryCode")
    exchange_status: Optional[str] = Field(None, alias="exchangeStatus")
    date_creation_str: Optional[str] = Field(None, alias="dateCreationStr") 
    date_last_update_str: Optional[str] = Field(None, alias="dateLastUpdateStr")
    date_last_validation_str: Optional[str] = Field(None, alias="dateLastValidationStr")
    date_expiry_str: Optional[str] = Field(None, alias="dateExpiryStr")
    comments: Optional[str] = None

    @validator('website', pre=True, allow_reuse=True)
    def _validate_website_str(cls, v):
        if v and not isinstance(v, HttpUrl):
            return HttpUrl(v) if isinstance(v, str) and v.startswith(('http', 'https')) else None
        return v
    
    class Config:
        allow_population_by_field_name = True

class MarketIdentifier(BaseModel):
    symbol: str
    name: Optional[str] = None
    asset_type: Optional[MarketAssetType] = Field(None, alias="assetType")
    currency: Optional[str] = None
    stock_exchange_info: Optional[StockExchangeInfo] = Field(None, alias="stockExchange")

    class Config:
        allow_population_by_field_name = True

class HistoricalPricePoint(BaseModel):
    date: datetime 
    open: float
    high: float
    low: float
    close: float
    adj_high: Optional[float] = None
    adj_low: Optional[float] = None
    adj_open: Optional[float] = None
    adj_close: Optional[float] = None 
    adj_volume: Optional[float] = None
    volume: float
    split_factor: Optional[float] = None
    dividend: Optional[float] = None
    symbol_from_eod: Optional[str] = Field(None, alias="symbol")
    exchange_mic_from_eod: Optional[str] = Field(None, alias="exchange")
    name_from_eod: Optional[str] = Field(None, alias="name")
    asset_type_from_eod: Optional[str] = Field(None, alias="asset_type")
    price_currency_from_eod: Optional[str] = Field(None, alias="price_currency")

    class Config:
        allow_population_by_field_name = True

class IntradayPricePoint(MarketIdentifier): # Inherits symbol. Name, asset_type, currency may be None from intraday feed.
    date: datetime                      # "date" from response (timestamp of the bar)
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None        # In MarketStack intraday, "close" is often the previous EOD close, or calculated.
    last: Optional[float] = None         # "last" from response (IEX last trade price in the interval)
    volume: Optional[float] = None
    exchange_mic_from_intraday: Optional[str] = Field(None, alias="exchange")


    # Fields specific to Marketstack's intraday or potentially IEX derived:
    mid: Optional[float] = None          # Midpoint price, often (bid+ask)/2
    last_size: Optional[float] = Field(None, alias="lastSize") 
    bid_price: Optional[float] = Field(None, alias="bidPrice") # Note: May be null if IEX entitlement not present
    bid_size: Optional[float] = Field(None, alias="bidSize")   # Note: May be null
    ask_price: Optional[float] = Field(None, alias="askPrice") # Note: May be null
    ask_size: Optional[float] = Field(None, alias="askSize")   # Note: May be null
    marketstack_last: Optional[float] = Field(None, alias="marketstackLast") # Marketstack's calculated last price
    
    @validator('symbol', pre=True, always=True)
    def set_symbol_if_not_present(cls, v, values):
        # If 'symbol' is not directly provided in the input data for IntradayPricePoint,
        # try to get it from the parent MarketIdentifier if it was populated by alias
        if v is None and 'symbol' in values: # 'symbol' might be in values if passed to MarketIdentifier part
            return values['symbol']
        # Or, if the API response for intraday uses a field named "symbol" directly (which it does)
        # and it wasn't picked by MarketIdentifier (e.g. if data is passed directly to IntradayPricePoint)
        # this validator ensures it's set on the model.
        # However, Pydantic usually handles aliasing well if `symbol` is in the input data.
        # This validator is more of a safeguard or for complex instantiation scenarios.
        # Given Marketstack provides "symbol", it should be directly mapped.
        return v

    class Config:
        allow_population_by_field_name = True

class EquityQuote(MarketIdentifier):
    price: float 
    change: Optional[float] = None
    percentChange: Optional[float] = None
    previousClose: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None
    adj_close: Optional[float] = None
    adj_open: Optional[float] = None
    timestamp: datetime
    averageVolume: Optional[float] = None
    marketCap: Optional[float] = None
    yearHigh: Optional[float] = None
    yearLow: Optional[float] = None
    tradingStatus: Optional[MarketTradingStatus] = None
    ask: Optional[float] = None
    bid: Optional[float] = None
    askSize: Optional[int] = None
    bidSize: Optional[int] = None
    eps: Optional[float] = None
    peRatio: Optional[float] = None
    beta: Optional[float] = None
    earningDate: Optional[datetime] = None
    dividend_eod: Optional[float] = Field(None, alias="dividend")
    split_factor_eod: Optional[float] = Field(None, alias="split_factor")

    class Config:
        allow_population_by_field_name = True

class KeyExecutive(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = Field(None, alias="function")
    salary: Optional[str] = None
    exercised: Optional[str] = None
    birth_year: Optional[str] = Field(None, alias="birthYear")
    
    class Config:
        allow_population_by_field_name = True

class CompanyAddress(BaseModel):
    street1: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state_or_country: Optional[str] = Field(None, alias="stateOrCountry")
    postal_code: Optional[str] = Field(None, alias="postalCode")
    state_or_country_description: Optional[str] = Field(None, alias="stateOrCountryDescription")

    class Config:
        allow_population_by_field_name = True
        
class CompanyProfile(MarketIdentifier):
    cik: Optional[str] = None
    isin: Optional[str] = None
    cusip: Optional[str] = None
    ein: Optional[str] = Field(None, alias="ein_employer_id")
    lei: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    sic_code: Optional[str] = Field(None, alias="sicCode")
    sic_name: Optional[str] = Field(None, alias="sicName")
    item_type: Optional[str] = Field(None, alias="itemType")
    about: Optional[str] = None
    website: Optional[HttpUrl] = Field(None, alias="website_str")
    full_time_employees: Optional[str] = Field(None, alias="fullTimeEmployees")
    ipo_date: Optional[date] = Field(None, alias="ipoDate")
    date_founded: Optional[date] = Field(None, alias="dateFounded")
    key_executives: Optional[List[KeyExecutive]] = Field(None, alias="keyExecutives")
    incorporation_state: Optional[str] = Field(None, alias="incorporation_description")
    fiscal_year_end: Optional[str] = Field(None, alias="end_fiscal")
    phone_number: Optional[str] = Field(None, alias="phone")
    address_details: Optional[CompanyAddress] = Field(None, alias="address")
    
    @validator('website', pre=True, allow_reuse=True)
    def _validate_profile_website_str(cls, v):
        if v and not isinstance(v, HttpUrl):
            return HttpUrl(v) if isinstance(v, str) and v.startswith(('http','https')) else None
        return v

    class Config:
        allow_population_by_field_name = True

# NewsArticle schema is kept for potential future use with other providers
class NewsArticle(BaseModel):
    id: str # Or UUID
    headline: str
    summary: Optional[str] = None
    source: str # e.g., "Reuters", "Bloomberg"
    url: HttpUrl
    publishedAt: datetime # Publication timestamp
    imageUrl: Optional[HttpUrl] = None
    symbols: Optional[List[str]] = None # Related stock symbols
    topics: Optional[List[str]] = None # e.g., ["earnings", "ipo"]
    sentiment: Optional[str] = None # e.g., "positive", "negative", "neutral"

class DividendData(MarketIdentifier):
    date: datetime 
    dividend_amount: float = Field(..., alias="dividend")
    payment_date: Optional[datetime] = Field(None, alias="paymentDate")
    record_date: Optional[datetime] = Field(None, alias="recordDate")
    declaration_date: Optional[datetime] = Field(None, alias="declarationDate")
    frequency: Optional[str] = Field(None, alias="distr_freq")

    class Config:
        allow_population_by_field_name = True
        
class StockSplitData(MarketIdentifier):
    date: datetime 
    split_factor: float = Field(..., alias="splitFactor")
    stock_split_ratio: Optional[str] = Field(None, alias="stock_split")

    class Config:
        allow_population_by_field_name = True

class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"

class OptionContract(MarketIdentifier):
    underlyingSymbol: str
    contractSymbol: str
    strikePrice: float
    expirationDate: date
    optionType: OptionType

class OptionQuote(OptionContract):
    price: float
    change: Optional[float] = None
    percentChange: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    openInterest: Optional[int] = None
    impliedVolatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None
    lastTradeTimestamp: Optional[datetime] = None

class ForexQuote(BaseModel):
    baseCurrency: str
    quoteCurrency: str
    pair: str
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    change: Optional[float] = None
    percentChange: Optional[float] = None
    timestamp: datetime

class CryptoQuote(BaseModel):
    baseAsset: str
    quoteAsset: str
    symbol: str
    price: float
    change24h: Optional[float] = None
    percentChange24h: Optional[float] = None
    volume24h: Optional[float] = None
    quoteVolume24h: Optional[float] = None
    marketCap: Optional[float] = None
    circulatingSupply: Optional[float] = None
    totalSupply: Optional[float] = None
    timestamp: datetime

class IndexQuote(MarketIdentifier):
    price: Optional[float] = None
    change: Optional[float] = None
    percentChange: Optional[float] = None
    timestamp: Optional[datetime] = None
    region: Optional[str] = None
    price_change_day_str: Optional[str] = Field(None, alias="price_change_day") 
    percentage_day_str: Optional[str] = Field(None, alias="percentage_day") 
    percentage_week_str: Optional[str] = Field(None, alias="percentage_week")
    percentage_month_str: Optional[str] = Field(None, alias="percentage_month")
    percentage_year_str: Optional[str] = Field(None, alias="percentage_year")
    index_info_date: Optional[date] = Field(None, alias="date")

    class Config:
        allow_population_by_field_name = True

class MarketMoverDirection(str, Enum):
    UP = "up"
    DOWN = "down"

class MarketMover(EquityQuote):
    rank: Optional[int] = None
    direction: Optional[MarketMoverDirection] = None

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: Optional[int] = None
    pageSize: Optional[int] = None
    totalItems: Optional[int] = None
    totalPages: Optional[int] = None

class MarketDataError(Exception):
    def __init__(self, message: str, symbol: Optional[str] = None, provider: Optional[str] = None, errorCode: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.symbol = symbol
        self.provider = provider
        self.errorCode = errorCode

    def __str__(self):
        return f"{self.provider or 'MarketData'} error (Code: {self.errorCode or 'N/A'}) for symbol '{self.symbol or 'N/A'}': {self.message}"
