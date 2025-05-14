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

/**
 * Represents a basic market identifier.
 */
export interface MarketIdentifier {
  symbol: string;
  exchange?: string; // e.g., NASDAQ, NYSE
  assetType?: MarketAssetType;
}

/**
 * Represents a single point of historical price data for an asset.
 */
export interface HistoricalPricePoint {
  date: string; // ISO 8601 date string (YYYY-MM-DD) or timestamp
  open: number;
  high: number;
  low: number;
  close: number;
  adjustedClose?: number; // Important for stocks considering dividends/splits
  volume: number;
}

/**
 * Represents real-time or delayed quote information for an equity (stock, ETF).
 */
export interface EquityQuote extends MarketIdentifier {
  price: number;
  change: number; // Absolute change from previous close
  percentChange: number; // Percentage change
  previousClose: number;
  open: number;
  high: number; // Day's high
  low: number; // Day's low
  volume: number;
  averageVolume?: number; // Average daily volume
  marketCap?: number;
  yearHigh?: number;
  yearLow?: number;
  timestamp: string; // ISO 8601 datetime string or timestamp of the last trade/update
  tradingStatus?: MarketTradingStatus;
  ask?: number;
  bid?: number;
  askSize?: number;
  bidSize?: number;
}

/**
 * Detailed profile information for a company or equity.
 */
export interface CompanyProfile extends MarketIdentifier {
  companyName: string;
  description?: string;
  industry?: string;
  sector?: string;
  website?: string;
  logoUrl?: string;
  ceo?: string;
  employees?: number;
  country?: string;
  currency?: string; // e.g., USD, EUR
  isin?: string; // International Securities Identification Number
  cusip?: string; // Committee on Uniform Security Identification Procedures number
}

/**
 * Represents a news article related to the market or a specific symbol.
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
 * Represents dividend information for an equity.
 */
export interface DividendData extends MarketIdentifier {
  exDividendDate?: string; // ISO 8601 date string
  paymentDate?: string; // ISO 8601 date string
  recordDate?: string; // ISO 8601 date string
  amount?: number; // Dividend per share
  frequency?: string; // e.g., "Quarterly", "Annually"
  yield?: number; // Dividend yield
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
  currency?: string;
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
 */
export interface IndexQuote extends MarketIdentifier {
  name: string;
  price: number;
  change: number;
  percentChange: number;
  previousClose?: number;
  open?: number;
  high?: number;
  low?: number;
  timestamp: string; // ISO 8601 datetime string
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
