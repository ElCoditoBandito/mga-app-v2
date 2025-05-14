# backend/schemas/market_data.py
from typing import List, Optional, TypeVar, Generic
from pydantic import BaseModel, HttpUrl
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
    OTHER = "OTHER" # Added as per user request

class MarketTradingStatus(str, Enum):
    PRE_MARKET = "PRE_MARKET"
    REGULAR_MARKET = "REGULAR_MARKET"
    POST_MARKET = "POST_MARKET"
    EXTENDED_HOURS = "EXTENDED_HOURS"
    CLOSED = "CLOSED"
    HALTED = "HALTED"
    UNKNOWN = "UNKNOWN"

class MarketIdentifier(BaseModel):
    symbol: str
    exchange: Optional[str] = None
    assetType: Optional[MarketAssetType] = None

class HistoricalPricePoint(BaseModel):
    date: datetime # Using datetime for flexibility, can be just date
    open: float
    high: float
    low: float
    close: float
    adjustedClose: Optional[float] = None
    volume: int

class EquityQuote(MarketIdentifier):
    price: float
    change: float
    percentChange: float
    previousClose: Optional[float] = None # Made optional as some basic quotes might not have it
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None # Made optional
    averageVolume: Optional[int] = None
    marketCap: Optional[float] = None
    yearHigh: Optional[float] = None
    yearLow: Optional[float] = None
    timestamp: datetime
    tradingStatus: Optional[MarketTradingStatus] = None
    ask: Optional[float] = None
    bid: Optional[float] = None
    askSize: Optional[int] = None
    bidSize: Optional[int] = None

class CompanyProfile(MarketIdentifier):
    companyName: str
    description: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    website: Optional[HttpUrl] = None
    logoUrl: Optional[HttpUrl] = None
    ceo: Optional[str] = None
    employees: Optional[int] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    isin: Optional[str] = None
    cusip: Optional[str] = None

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
    sentiment: Optional[str] = None # 'positive', 'negative', 'neutral'

class DividendData(MarketIdentifier):
    exDividendDate: Optional[date] = None
    paymentDate: Optional[date] = None
    recordDate: Optional[date] = None
    amount: Optional[float] = None
    frequency: Optional[str] = None
    yield_value: Optional[float] = None # Renamed from yield to avoid conflict with keyword

class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"

class OptionContract(MarketIdentifier):
    underlyingSymbol: str
    contractSymbol: str
    strikePrice: float
    expirationDate: date
    optionType: OptionType
    currency: Optional[str] = None

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
    symbol: str # e.g., BTCUSD or just BTC
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
    name: str
    price: float
    change: Optional[float] = None
    percentChange: Optional[float] = None
    previousClose: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    timestamp: datetime

class MarketMoverDirection(str, Enum):
    UP = "up"
    DOWN = "down"

class MarketMover(EquityQuote):
    rank: Optional[int] = None # Rank in the list
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
    errorCode: Optional[str] = None # Kept as str for flexibility
