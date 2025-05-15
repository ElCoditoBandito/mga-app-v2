// Market data types for frontend consumption

// Enums
export enum MarketAssetType {
  STOCK = "Stock",
  ETF = "ETF",
  INDEX = "Index",
  MUTUAL_FUND = "Mutual Fund",
  FOREX = "Forex",
  CRYPTO = "Crypto",
  COMMODITY = "Commodity",
  BOND = "Bond",
  OPTION = "Option",
  FUTURE = "Future"
}

// Phase 1 - Core Market Data Types

export interface StockHistoricalDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  adj_high?: number;
  adj_low?: number;
  adj_open?: number;
  adj_close?: number;
  adj_volume?: number;
  split_factor?: number;
  dividend?: number;
  symbol?: string;
  exchange?: string;
  name?: string;
  asset_type?: string;
  price_currency?: string;
}

export interface StockHistoricalData {
  symbol: string;
  name: string;
  exchange: string;
  data: StockHistoricalDataPoint[];
}

export interface EquityQuote {
  symbol: string;
  name: string;
  exchange: string; // MIC code
  price: number; // Latest adj_close
  change: number;
  percent_change: number;
  volume: number;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  adj_open?: number;
  adj_close?: number;
  dividend?: number;
  split_factor?: number;
  asset_type: string;
  price_currency: string;
  // Optional fields that might be populated from company profile
  marketCap?: number;
  yearHigh?: number;
  yearLow?: number;
  eps?: number;
  peRatio?: number;
}

export interface IntradayPricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  symbol: string;
  exchange: string; // MIC code
  // Optional fields that might be null due to IEX entitlement
  mid?: number;
  last_size?: number;
  bid_size?: number;
  bid_price?: number;
  ask_price?: number;
  ask_size?: number;
  last?: number;
  marketstack_last?: number;
}

export interface StockExchangeInfo {
  name: string;
  acronym: string;
  mic: string;
  country?: string;
  country_code?: string;
  city?: string;
  website?: string;
  operating_mic?: string;
  oprt_sgmt?: string;
  legal_entity_name?: string;
  exchange_lei?: string;
  market_category_code?: string;
  exchange_status?: string;
  date_creation?: string;
  date_last_update?: string;
  date_last_validation?: string;
  date_expiry?: string;
  comments?: string;
}

export interface CompanyAddress {
  street1?: string;
  street2?: string;
  city?: string;
  postal_code?: string;
  stateOrCountry?: string;
  state_or_country_description?: string;
}

export interface KeyExecutive {
  name: string;
  salary?: string;
  function?: string;
  exercised?: string;
  birth_year?: string;
}

export interface CompanyProfile {
  symbol: string;
  name: string;
  stockExchangeInfo: StockExchangeInfo;
  assetType: string;
  currency?: string;
  about?: string;
  industry?: string;
  sector?: string;
  website?: string;
  fullTimeEmployees?: number;
  ipoDate?: string;
  dateFounded?: string;
  addressDetails?: CompanyAddress;
  phoneNumber?: string;
  keyExecutives?: KeyExecutive[];
  cik?: string;
  isin?: string;
  cusip?: string;
  ein?: string;
  lei?: string;
  sicCode?: string;
  sicName?: string;
  itemType?: string;
  // Additional fields from tickerinfo
  incorporation?: string;
  incorporation_description?: string;
  start_fiscal?: string;
  end_fiscal?: string;
  reporting_currency?: string;
  post_address?: CompanyAddress;
  previous_names?: Array<{name: string, from: string}>;
  mission?: string;
  vision?: string;
}

export interface DividendData {
  date: string;
  dividend: number;
  symbol: string;
  payment_date?: string;
  record_date?: string;
  declaration_date?: string;
  distr_freq?: string; // e.g., "q" for quarterly
}

export interface StockSplitData {
  date: string;
  split_factor: number;
  symbol: string;
  stock_split: string; // e.g., "4:1"
}

export interface OptionQuote {
  contract_symbol: string;
  underlying_symbol: string;
  expiration_date: string;
  strike_price: number;
  option_type: "call" | "put";
  last_price: number;
  bid: number;
  ask: number;
  volume: number;
  open_interest: number;
  implied_volatility: number;
  delta?: number;
  gamma?: number;
  theta?: number;
  vega?: number;
  rho?: number;
  timestamp: string;
}

export interface ForexQuote {
  base_currency: string;
  quote_currency: string;
  rate: number;
  timestamp: string;
  change?: number;
  percent_change?: number;
}

export interface CryptoQuote {
  base_asset: string;
  quote_asset: string;
  price: number;
  volume_24h: number;
  market_cap?: number;
  change_24h: number;
  percent_change_24h: number;
  timestamp: string;
}

export interface MarketMover {
  symbol: string;
  name: string;
  exchange: string;
  price: number;
  change: number;
  percent_change: number;
  volume: number;
  market_cap?: number;
  timestamp: string;
}

export interface IndexQuote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  percent_change: number;
  timestamp: string;
  // Additional fields from MarketStack's /indexinfo
  region?: string;
  country?: string;
  percentage_week?: string;
  percentage_month?: string;
  percentage_year?: string;
}

export interface RealtimeStockPrice {
  exchange_code: string;
  exchange_name: string;
  country: string;
  ticker: string;
  price: string;
  currency: string;
  trade_last: string;
}

export interface TickerSearchResultItem {
  name: string;
  ticker: string;
  has_intraday: boolean;
  has_eod: boolean;
  stock_exchange: {
    name: string;
    acronym: string;
    mic: string;
  };
}

export interface CurrencyInfo {
  code: string;
  name: string;
  symbol: string;
  symbol_native: string;
}

export interface TimezoneInfo {
  timezone: string;
  abbr: string;
  abbr_dst: string;
}

// Phase 2 - Commodity Prices
export interface CommodityPrice {
  commodity_name: string;
  commodity_unit: string;
  commodity_price: number;
  price_change_day: number;
  percentage_day: number;
  percentage_week: number;
  percentage_month: number;
  percentage_year: number;
  quarter1_25: number;
  quarter2_25: number;
  quarter3_25: number;
  quarter4_25: number;
  quarter1_24: number;
  quarter2_24: number;
  quarter3_24: number;
  quarter4_24: number;
  quarter1_23: number;
  quarter2_23: number;
  quarter3_23: number;
  quarter4_23: number;
  datetime: string;
}

// Phase 2 - Historical Commodity Prices
export interface HistoricalCommodityPriceData {
  basics: {
    commodity_name: string;
    commodity_unit: string;
  };
  data: CommodityPricePoint[];
}

export interface CommodityPricePoint {
  commodity_price: number;
  date: string;
}

// Phase 2 - Company Ratings
export interface CompanyRatingData {
  status: string;
  result: {
    basics: {
      ticker: string;
      name: string;
      exchange: string;
    };
    output: {
      analyst_consensus: AnalystConsensus;
      analysts: AnalystRatingDetail[];
    };
  };
}

export interface AnalystConsensus {
  buy: number;
  hold: number;
  sell: number;
  average_rating: number;
  average_target_price: number;
  high_target_price: number;
  low_target_price: number;
  median_target_price: number;
}

export interface AnalystRatingDetail {
  analyst_name: string;
  analyst_rating: string;
  target_price: number;
  rating_date: string;
}

// Phase 2 - Stock Market Index Listing
export interface IndexBasicInfo {
  benchmark: string;
  name: string;
  country: string;
  currency: string;
}

// Phase 2 - Bonds Data
export interface BondCountry {
  country: string;
}

export interface BondInfoData {
  region: string;
  country: string;
  type: string;
  yield: number;
  price_change_day: number;
  percentage_week: number;
  percentage_month: number;
  percentage_year: number;
  datetime: string;
}

// Phase 2 - ETF Data
export interface ETFTicker {
  ticker: string;
}

export interface ETFHoldingDetails {
  basics: {
    ticker: string;
    name: string;
    exchange: string;
  };
  output: {
    attributes: {
      aum: number;
      expense_ratio: number;
      shares_outstanding: number;
      nav: number;
    };
    signature: {
      sector_weights: {
        sector: string;
        weight: number;
      }[];
    };
    holdings: {
      ticker: string;
      name: string;
      weight: number;
      shares: number;
      market_value: number;
    }[];
  };
}

// Legacy types - keeping for backward compatibility
export interface StockQuote {
  symbol: string;
  name: string;
  exchange: string;
  price: number;
  change: number;
  percent_change: number;
  volume: number;
  timestamp: string;
}

export interface ForexRate {
  base_currency: string;
  quote_currency: string;
  rate: number;
  timestamp: string;
}
