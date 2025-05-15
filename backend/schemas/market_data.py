from datetime import date, datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


# Enums
class MarketAssetType(str, Enum):
    STOCK = "Stock"
    ETF = "ETF"
    INDEX = "Index"
    MUTUAL_FUND = "Mutual Fund"
    FOREX = "Forex"
    CRYPTO = "Crypto"
    COMMODITY = "Commodity"
    BOND = "Bond"
    OPTION = "Option"
    FUTURE = "Future"


# Phase 1 - Historical Price Data Models
class HistoricalPricePoint(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    adj_high: float
    adj_low: float
    adj_open: float
    adj_close: float
    adj_volume: int
    split_factor: float
    dividend: float
    symbol: str
    exchange: str  # MIC code
    name: str
    asset_type: str
    price_currency: str


# Phase 1 - Equity Quote Model
class EquityQuote(BaseModel):
    symbol: str
    name: str
    exchange: str  # MIC code
    price: float  # Latest adj_close
    change: float
    percent_change: float
    volume: int
    timestamp: datetime
    open: float
    high: float
    low: float
    adj_open: float
    adj_close: float
    dividend: Optional[float] = None
    split_factor: Optional[float] = None
    asset_type: str
    price_currency: str


# Phase 1 - Intraday Price Data Model
class IntradayPricePoint(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    exchange: str  # MIC code
    # Optional fields that might be null due to IEX entitlement
    mid: Optional[float] = None
    last_size: Optional[int] = None
    bid_size: Optional[float] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    ask_size: Optional[float] = None
    last: Optional[float] = None
    marketstack_last: Optional[float] = None


# Phase 1 - Company Profile Models
class StockExchangeInfo(BaseModel):
    name: str
    acronym: str
    mic: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    website: Optional[str] = None


class CompanyAddress(BaseModel):
    street1: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    stateOrCountry: Optional[str] = None
    state_or_country_description: Optional[str] = None


class KeyExecutive(BaseModel):
    name: str
    salary: Optional[str] = None
    function: Optional[str] = None
    exercised: Optional[str] = None
    birth_year: Optional[str] = None


class CompanyProfile(BaseModel):
    symbol: str
    name: str
    stock_exchange_info: StockExchangeInfo
    asset_type: str = "equity"
    currency: Optional[str] = None
    about: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    website: Optional[str] = None
    full_time_employees: Optional[int] = None
    ipo_date: Optional[date] = None
    date_founded: Optional[date] = None
    address_details: Optional[CompanyAddress] = None
    phone_number: Optional[str] = None
    key_executives: Optional[List[KeyExecutive]] = None
    cik: Optional[str] = None
    isin: Optional[str] = None
    cusip: Optional[str] = None
    ein: Optional[str] = None
    lei: Optional[str] = None
    sic_code: Optional[str] = None
    sic_name: Optional[str] = None
    item_type: Optional[str] = None


# Phase 1 - Dividend Data Model
class DividendData(BaseModel):
    date: datetime
    dividend: float
    symbol: str
    payment_date: Optional[datetime] = None
    record_date: Optional[datetime] = None
    declaration_date: Optional[datetime] = None
    distr_freq: Optional[str] = None  # e.g., "q" for quarterly


# Phase 1 - Stock Split Data Model
class StockSplitData(BaseModel):
    date: date
    split_factor: float
    symbol: str
    stock_split: str  # e.g., "4:1"


# Phase 1 - Option Quote Model
class OptionQuote(BaseModel):
    contract_symbol: str
    underlying_symbol: str
    expiration_date: date
    strike_price: float
    option_type: Literal["call", "put"]
    last_price: float
    bid: float
    ask: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None
    timestamp: datetime


# Phase 1 - Forex Quote Model
class ForexQuote(BaseModel):
    base_currency: str
    quote_currency: str
    rate: float
    timestamp: datetime
    change: Optional[float] = None
    percent_change: Optional[float] = None


# Phase 1 - Crypto Quote Model
class CryptoQuote(BaseModel):
    base_asset: str
    quote_asset: str
    price: float
    volume_24h: float
    market_cap: Optional[float] = None
    change_24h: float
    percent_change_24h: float
    timestamp: datetime


# Phase 1 - Market Mover Model
class MarketMover(BaseModel):
    symbol: str
    name: str
    exchange: str
    price: float
    change: float
    percent_change: float
    volume: int
    market_cap: Optional[float] = None
    timestamp: datetime


# Stock Quote Models
class StockQuote(BaseModel):
    symbol: str
    name: str
    exchange: str
    price: float
    change: float
    percent_change: float
    volume: int
    timestamp: datetime


class StockQuoteResponse(BaseModel):
    data: StockQuote


# Historical Stock Data Models
class StockHistoricalDataPoint(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockHistoricalData(BaseModel):
    symbol: str
    name: str
    exchange: str
    data: List[StockHistoricalDataPoint]


class StockHistoricalDataResponse(BaseModel):
    data: StockHistoricalData


# Index Quote Models
class IndexQuote(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    percent_change: float
    timestamp: datetime


class IndexQuoteResponse(BaseModel):
    data: IndexQuote


# Forex Rate Models
class ForexRate(BaseModel):
    base_currency: str
    quote_currency: str
    rate: float
    timestamp: datetime


class ForexRateResponse(BaseModel):
    data: ForexRate


# Phase 2 - Commodity Price Models
class CommodityPrice(BaseModel):
    commodity_name: str
    commodity_unit: str
    commodity_price: float
    price_change_day: float
    percentage_day: float
    percentage_week: float
    percentage_month: float
    percentage_year: float
    quarter1_25: float
    quarter2_25: float
    quarter3_25: float
    quarter4_25: float
    quarter1_24: float
    quarter2_24: float
    quarter3_24: float
    quarter4_24: float
    quarter1_23: float
    quarter2_23: float
    quarter3_23: float
    quarter4_23: float
    datetime: datetime


class CommodityPriceResponse(BaseModel):
    data: CommodityPrice


# Phase 2 - Historical Commodity Price Models
class CommodityPricePoint(BaseModel):
    commodity_price: float
    date: datetime


class CommodityBasics(BaseModel):
    commodity_name: str
    commodity_unit: str


class HistoricalCommodityPriceData(BaseModel):
    basics: CommodityBasics
    data: List[CommodityPricePoint]


class HistoricalCommodityPriceResponse(BaseModel):
    data: HistoricalCommodityPriceData


# Phase 2 - Company Ratings Models
class AnalystConsensus(BaseModel):
    buy: int
    hold: int
    sell: int
    average_rating: float
    average_target_price: float
    high_target_price: float
    low_target_price: float
    median_target_price: float


class AnalystRatingDetail(BaseModel):
    analyst_name: str
    analyst_rating: str
    target_price: float
    rating_date: datetime


class CompanyRatingOutput(BaseModel):
    analyst_consensus: AnalystConsensus
    analysts: List[AnalystRatingDetail]


class CompanyBasics(BaseModel):
    ticker: str
    name: str
    exchange: str


class CompanyRatingResult(BaseModel):
    basics: CompanyBasics
    output: CompanyRatingOutput


class CompanyRatingData(BaseModel):
    status: str
    result: CompanyRatingResult


class CompanyRatingResponse(BaseModel):
    data: CompanyRatingData


# Phase 2 - Stock Market Index Listing Models
class IndexBasicInfo(BaseModel):
    benchmark: str
    name: str
    country: str
    currency: str


class IndexListResponse(BaseModel):
    data: List[IndexBasicInfo]


# Phase 2 - Bonds Data Models
class BondCountry(BaseModel):
    country: str


class BondCountryListResponse(BaseModel):
    data: List[BondCountry]


class BondInfoData(BaseModel):
    region: str
    country: str
    type: str
    yield_value: float = Field(..., alias="yield")
    price_change_day: float
    percentage_week: float
    percentage_month: float
    percentage_year: float
    datetime: datetime


class BondInfoResponse(BaseModel):
    data: BondInfoData


# Phase 2 - ETF Data Models
class ETFTicker(BaseModel):
    ticker: str


class ETFTickerListResponse(BaseModel):
    data: List[ETFTicker]


class ETFAttributes(BaseModel):
    aum: float
    expense_ratio: float
    shares_outstanding: float
    nav: float


class SectorWeight(BaseModel):
    sector: str
    weight: float


class ETFSignature(BaseModel):
    sector_weights: List[SectorWeight]


class ETFHolding(BaseModel):
    ticker: str
    name: str
    weight: float
    shares: int
    market_value: float


class ETFOutput(BaseModel):
    attributes: ETFAttributes
    signature: ETFSignature
    holdings: List[ETFHolding]


class ETFBasics(BaseModel):
    ticker: str
    name: str
    exchange: str


class ETFHoldingDetails(BaseModel):
    basics: ETFBasics
    output: ETFOutput


class ETFHoldingResponse(BaseModel):
    data: ETFHoldingDetails
