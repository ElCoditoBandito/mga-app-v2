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
    name: Optional[str] = None # Full exchange name from /tickers > stock_exchange > name
    acronym: Optional[str] = None # e.g., "NASDAQ" from /tickers > stock_exchange > acronym
    mic: Optional[str] = None # Market Identifier Code from /tickers > stock_exchange > mic
    country: Optional[str] = None # From /tickers > stock_exchange > country
    country_code: Optional[str] = Field(None, alias="countryCode") # From /tickers > stock_exchange > country_code
    city: Optional[str] = None # From /tickers > stock_exchange > city
    website: Optional[HttpUrl] = Field(None, alias="website_str") # Field name in MS is 'website', ensure it's parsed to HttpUrl

    @validator('website', pre=True, allow_reuse=True)
    def _validate_website_str(cls, v):
        if v and not isinstance(v, HttpUrl):
            return HttpUrl(v) if isinstance(v, str) and v.startswith(('http', 'https')) else None
        return v

class MarketIdentifier(BaseModel):
    symbol: str
    name: Optional[str] = None # From EOD > name OR /tickers > name OR /tickerinfo > name
    asset_type: Optional[MarketAssetType] = Field(None, alias="assetType") # From EOD > asset_type
    currency: Optional[str] = None # From EOD > price_currency OR /tickerinfo > reporting_currency
    stock_exchange_info: Optional[StockExchangeInfo] = Field(None, alias="stockExchange") # From /tickers > stock_exchange

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
    # Fields from Marketstack EOD item directly
    symbol_from_eod: Optional[str] = Field(None, alias="symbol")
    exchange_mic_from_eod: Optional[str] = Field(None, alias="exchange")
    name_from_eod: Optional[str] = Field(None, alias="name")
    asset_type_from_eod: Optional[str] = Field(None, alias="asset_type") # Raw string from provider
    price_currency_from_eod: Optional[str] = Field(None, alias="price_currency")

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
    adj_close: Optional[float] = None # From EOD
    adj_open: Optional[float] = None # From EOD
    timestamp: datetime # Date of the EOD data
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
    dividend_eod: Optional[float] = Field(None, alias="dividend") # From EOD data point
    split_factor_eod: Optional[float] = Field(None, alias="split_factor") # From EOD data point

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
    website: Optional[HttpUrl] = Field(None, alias="website_str") # using alias for validator
    full_time_employees: Optional[str] = Field(None, alias="fullTimeEmployees")
    ipo_date: Optional[date] = Field(None, alias="ipoDate")
    date_founded: Optional[date] = Field(None, alias="dateFounded")
    key_executives: Optional[List[KeyExecutive]] = Field(None, alias="keyExecutives")
    incorporation_state: Optional[str] = Field(None, alias="incorporation_description") # from tickerinfo
    fiscal_year_end: Optional[str] = Field(None, alias="end_fiscal")
    phone_number: Optional[str] = Field(None, alias="phone")
    address_details: Optional[CompanyAddress] = Field(None, alias="address") # From /tickerinfo
    
    @validator('website', pre=True, allow_reuse=True)
    def _validate_profile_website_str(cls, v):
        if v and not isinstance(v, HttpUrl):
            return HttpUrl(v) if isinstance(v, str) and v.startswith(('http','https')) else None
        return v

    class Config:
        allow_population_by_field_name = True

class NewsArticle(BaseModel):
    id: str
    headline: str
    summary: Optional[str] = None
    source: str
    url: HttpUrl
    publishedAt: datetime
    imageUrl: Optional[HttpUrl] = None
    symbols: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    sentiment: Optional[str] = None

class DividendData(MarketIdentifier):
    date: datetime # Primary date from MarketStack dividend entry
    dividend_amount: float = Field(..., alias="dividend")
    payment_date: Optional[datetime] = Field(None, alias="paymentDate")
    record_date: Optional[datetime] = Field(None, alias="recordDate")
    declaration_date: Optional[datetime] = Field(None, alias="declarationDate")
    frequency: Optional[str] = Field(None, alias="distr_freq")

    class Config:
        allow_population_by_field_name = True
        
class StockSplitData(MarketIdentifier):
    date: datetime # Date of the split from MarketStack
    split_factor: float = Field(..., alias="splitFactor")
    stock_split_ratio: Optional[str] = Field(None, alias="stock_split") # e.g., "4:1"

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
    timestamp: Optional[datetime] = None # For EOD data, this is the EOD timestamp.
                                      # For /indexinfo, it's the 'date' field.
    # From /indexinfo specific response
    region: Optional[str] = None
    price_change_day_str: Optional[str] = Field(None, alias="price_change_day") 
    percentage_day_str: Optional[str] = Field(None, alias="percentage_day") 
    percentage_week_str: Optional[str] = Field(None, alias="percentage_week")
    percentage_month_str: Optional[str] = Field(None, alias="percentage_month")
    percentage_year_str: Optional[str] = Field(None, alias="percentage_year")
    index_info_date: Optional[date] = Field(None, alias="date") # from /indexinfo 'date' field

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

class MarketDataError(BaseModel):
    symbol: Optional[str] = None
    message: str
    provider: Optional[str] = None
    errorCode: Optional[str] = None
