// frontend/src/types/market.ts

/**
 * Defines the type of asset. This might overlap with backend enums,
 * but is useful for typing market data responses.
 */
export enum MarketAssetType {
  STOCK = 'STOCK',
  ETF = 'ETF',
  MUTUAL_FUND = 'MUTUAL_FUND',
  OPTION = 'OPTION',
  CRYPTO = 'CRYPTO',
  FOREX = 'FOREX',
  INDEX = 'INDEX',
  BOND = 'BOND',
  COMMODITY = 'COMMODITY',
  OTHER = 'OTHER',
}

/**
 * Represents the current status of a market or an asset's trading session.
 */
export enum MarketTradingStatus {
  PRE_MARKET = 'PRE_MARKET',
  REGULAR_MARKET = 'REGULAR_MARKET', // Open
  POST_MARKET = 'POST_MARKET',
  EXTENDED_HOURS = 'EXTENDED_HOURS',
  CLOSED = 'CLOSED',
  HALTED = 'HALTED',
  UNKNOWN = 'UNKNOWN',
}

export interface StockExchangeInfo {
  name?: string; // Full exchange name (e.g., "NASDAQ - ALL MARKETS")
  acronym?: string; // e.g., "NASDAQ"
  mic?: string; // Market Identifier Code (e.g., "XNAS")
  country?: string;
  countryCode?: string; // e.g., "US"
  city?: string;
  website?: string;
}

/**
 * Represents a basic market identifier. Enriched based on MarketStack v2 EOD and Ticker responses.
 */
export interface MarketIdentifier {
  symbol: string;
  name?: string; // Common name of the asset (e.g., "Apple Inc", from EOD response or /tickers)
  assetType?: MarketAssetType; // e.g. "Stock" from EOD response
  currency?: string; // Reporting currency (e.g., "USD", from EOD or /tickers response)
  stockExchange?: StockExchangeInfo; // Detailed exchange info from /tickers response
}

/**
 * Represents a single point of historical price data for an asset.
 * Fields align with MarketStack EOD response.
 */
export interface HistoricalPricePoint {
  date: string; // ISO 8601 datetime string (MarketStack: "YYYY-MM-DDTHH:MM:SS+0000")
  open: number;
  high: number;
  low: number;
  close: number;
  adj_high?: number; // From MarketStack EOD
  adj_low?: number; // From MarketStack EOD
  adj_open?: number; // From MarketStack EOD
  adj_close?: number; // From MarketStack EOD (use as primary adjusted close)
  adj_volume?: number; // From MarketStack EOD
  volume: number;
  split_factor?: number; // From MarketStack EOD
  dividend?: number; // Dividend paid on this date, from MarketStack EOD
  symbol?: string; // Included in EOD data items
  exchange?: string; // MIC, included in EOD data items (maps to stockExchange.mic)
  // MarketStack EOD also includes name, asset_type, price_currency directly in each data point
  name_in_eod?: string; // 'name' from EOD data point
  asset_type_in_eod?: string; // 'asset_type' from EOD data point
  price_currency_in_eod?: string; // 'price_currency' from EOD data point
}

/**
 * Represents real-time or delayed quote information for an equity (stock, ETF).
 * This will be primarily based on MarketStack EOD data for now due to v2 intraday/real-time limitations.
 */
export interface EquityQuote extends MarketIdentifier {
  price: number; // Typically the 'close' or 'adj_close' from latest EOD
  change?: number; // Calculated: price - previousClose
  percentChange?: number; // Calculated: (change / previousClose) * 100
  previousClose?: number; // adj_open or open from previous day, or calculated from change
  open?: number; // From EOD
  high?: number; // Day's high from EOD
  low?: number; // Day's low from EOD
  volume?: number; // From EOD
  adj_close?: number; // From EOD - useful for calculations
  adj_open?: number; // From EOD
  timestamp: string; // Date of the EOD data
  
  // Fields that are less likely from basic EOD, more from profile or specialized quote endpoints
  averageVolume?: number; 
  marketCap?: number;
  yearHigh?: number; // 52-week high
  yearLow?: number; // 52-week low
  tradingStatus?: MarketTradingStatus; // Hard to determine from EOD, might be inferred or from another source
  ask?: number; // Not typically in EOD
  bid?: number; // Not typically in EOD
  askSize?: number;
  bidSize?: number;
  eps?: number; // Earnings Per Share (TTM)
  peRatio?: number; // Price to Earnings Ratio
  beta?: number; // Stock's volatility
  earningDate?: string; // ISO 8601
  dividend_eod?: number; // Dividend amount directly from EOD if available
  split_factor_eod?: number; // Split factor directly from EOD if available
}

export interface KeyExecutive {
  name?: string;
  title?: string; // MarketStack uses "function"
  salary?: string; // MarketStack returns as string e.g. "3.36M"
  exercised?: string;
  birthYear?: string;
}

/**
 * Detailed profile information for a company or equity.
 * Expanded based on MarketStack v2 /tickerinfo and /tickers/{symbol} responses.
 */
export interface CompanyProfile extends MarketIdentifier {
  // name, symbol, currency, stockExchange are from MarketIdentifier
  cik?: string; // From /tickers/{symbol} & /tickerinfo
  isin?: string; // From /tickers/{symbol}
  cusip?: string; // From /tickers/{symbol}
  ein?: string; // Employer ID Number, from /tickers/{symbol} (ein_employer_id)
  lei?: string; // Legal Entity Identifier, from /tickers/{symbol}
  
  sector?: string; // From /tickers/{symbol} & /tickerinfo
  industry?: string; // From /tickers/{symbol} & /tickerinfo
  sicCode?: string; // From /tickers/{symbol} (sic_code)
  sicName?: string; // From /tickers/{symbol} (sic_name)
  itemType?: string; // e.g. "equity", from /tickers/{symbol}

  // From /tickerinfo
  about?: string; // Company description (long description)
  website?: string;
  fullTimeEmployees?: string; // MarketStack returns as string, e.g., "221000"
  ipoDate?: string; // ISO 8601 date string
  dateFounded?: string; // ISO 8601 date string
  keyExecutives?: KeyExecutive[];
  incorporationState?: string; // MarketStack: incorporation_description or address.stateOrCountryDescription
  fiscalYearEnd?: string; // MarketStack: end_fiscal (e.g., "0630" for June 30th)
  phoneNumber?: string;
  address?: {
    street1?: string;
    street2?: string;
    city?: string;
    stateOrCountry?: string; // MarketStack: stateOrCountryDescription or stateOrCountry
    postalCode?: string;
  };
  // Future expansion: analystRatings from /companyratings, detailed financials
}


/**
 * Represents a news article related to the market or a specific symbol.
 * (MarketStack v2 does not seem to have a general news endpoint like v1)
 */
export interface NewsArticle {
  id: string; // Unique identifier for the news article
  headline: string;
  summary?: string;
  source: string; // e.g., "Reuters", "Bloomberg"
  url: string;
  publishedAt: string; // ISO 8601 datetime string
  imageUrl?: string;
  symbols?: string[]; // Symbols mentioned or relevant to the article
  topics?: string[]; // e.g., "earnings", "ipo"
  sentiment?: 'positive' | 'negative' | 'neutral';
}

/**
 * Represents dividend information for an equity. Based on MarketStack v2 /dividends response.
 */
export interface DividendData extends MarketIdentifier {
  // symbol is inherited
  date: string; // Date of the dividend event (MarketStack uses this as the primary date for the entry)
  dividendAmount: number; // 'dividend' field from MarketStack
  payment_date?: string; // 'payment_date' from MarketStack (ISO 8601 datetime)
  record_date?: string; // 'record_date' from MarketStack (ISO 8601 datetime)
  declaration_date?: string; // 'declaration_date' from MarketStack (ISO 8601 datetime)
  frequency?: string; // 'distr_freq' from MarketStack (e.g., 'q' for quarterly)
}

/**
 * Represents stock split information. Based on MarketStack v2 /splits response.
 */
export interface StockSplitData extends MarketIdentifier {
  // symbol is inherited
  date: string; // Date of the split (YYYY-MM-DD)
  splitFactor: number; // e.g., 4.0 for a 4:1 split (from 'split_factor')
  stockSplitRatio?: string; // Text representation, e.g., "4:1" (from 'stock_split')
}


/**
 * Represents an options contract.
 */
export interface OptionContract extends MarketIdentifier {
  underlyingSymbol: string;
  contractSymbol: string; // The specific option symbol
  strikePrice: number;
  expirationDate: string; // ISO 8601 date string
  optionType: 'call' | 'put';
}

/**
 * Represents quote information for an options contract.
 */
export interface OptionQuote extends OptionContract {
  price: number; // Last trade price
  change: number;
  percentChange: number;
  bid: number;
  ask: number;
  volume: number;
  openInterest: number;
  impliedVolatility?: number;
  delta?: number;
  gamma?: number;
  theta?: number;
  vega?: number;
  rho?: number;
  lastTradeTimestamp: string; // ISO 8601 datetime string
}

/**
 * Represents a Forex (currency pair) quote.
 */
export interface ForexQuote {
  baseCurrency: string; // e.g., EUR
  quoteCurrency: string; // e.g., USD
  pair: string; // e.g., EURUSD
  price: number;
  bid: number;
  ask: number;
  change: number;
  percentChange: number;
  timestamp: string; // ISO 8601 datetime string
}

/**
 * Represents a cryptocurrency quote.
 */
export interface CryptoQuote {
  baseAsset: string; // e.g., BTC
  quoteAsset: string; // e.g., USD
  symbol: string; // e.g., BTCUSD or BTC
  price: number;
  change24h: number; // Change in the last 24 hours
  percentChange24h: number;
  volume24h: number; // Volume in base asset
  quoteVolume24h?: number; // Volume in quote asset
  marketCap?: number;
  circulatingSupply?: number;
  totalSupply?: number;
  timestamp: string; // ISO 8601 datetime string
}

/**
 * Represents an index quote (e.g., S&P 500, NASDAQ Composite).
 * Uses MarketStack /indexinfo or /eod for an index symbol.
 */
export interface IndexQuote extends MarketIdentifier {
  // name is inherited
  price?: number; // Current price
  change?: number; // Calculated or from price_change_day
  percentChange?: number; // Calculated or from percentage_day
  timestamp?: string; // ISO 8601 datetime string from 'date' in indexinfo
  // From /indexinfo
  region?: string;
  price_change_day_str?: string; // From indexinfo (string, e.g., "71")
  percentage_day_str?: string; // From indexinfo (string, e.g., "0.84%")
  percentage_week_str?: string;
  percentage_month_str?: string;
  percentage_year_str?: string;
}

/**
 * Represents a market mover (e.g., top gainer, top loser).
 */
export interface MarketMover extends EquityQuote {
  rank: number; // Rank in the list (e.g., 1st top gainer)
  direction: 'up' | 'down';
}

/**
 * General purpose structure for API responses that might be paginated.
 */
export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

/**
 * Generic error structure for market data operations.
 */
export interface MarketDataError {
  symbol?: string;
  message: string;
  provider?: string; // 'AlphaVantage', 'MarketStack', etc.
  errorCode?: string | number; // Provider-specific error code
}
