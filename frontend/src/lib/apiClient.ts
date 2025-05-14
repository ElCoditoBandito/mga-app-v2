// src/lib/apiClient.ts
import type { Auth0ContextInterface } from "@auth0/auth0-react";

// Define a type for the getAccessTokenSilently function
type GetAccessTokenSilentlyType = Auth0ContextInterface['getAccessTokenSilently'];

// Custom API error class
export class ApiError extends Error {
  status: number;
  response: Response;

  constructor(message: string, status: number, response: Response) {
    super(message);
    this.status = status;
    this.response = response;
    this.name = 'ApiError';
  }
}

// Function to create an authenticated fetch wrapper
export const createApiClient = (getAccessTokenSilently: GetAccessTokenSilentlyType) => {
  const baseURL = import.meta.env.VITE_API_URL;

  if (!baseURL) {
    throw new Error("VITE_API_URL is not defined in environment variables.");
  }

  return async (endpoint: string, options: RequestInit = {}): Promise<Response> => {
    console.log(`API Client: Preparing request to ${endpoint}`);
    let token: string | undefined;
    try {
      console.log(`API Client: Getting access token for audience: ${import.meta.env.VITE_AUTH0_AUDIENCE}`);
      token = await getAccessTokenSilently({
        authorizationParams: {
          audience: import.meta.env.VITE_AUTH0_AUDIENCE,
        },
      });
      console.log(`API Client: Successfully obtained access token`);
    } catch (error) {
      console.error("Error getting access token:", error);
      throw new Error("Failed to get authentication token.");
    }

    const headers = new Headers(options.headers);
    headers.set('Authorization', `Bearer ${token}`);
    // Add content-type header if sending JSON data
    if (options.body && typeof options.body === 'string' && (!options.headers || !('Content-Type' in options.headers))) {
      try {
        JSON.parse(options.body); // Check if it's valid JSON
        headers.set('Content-Type', 'application/json');
      } catch (e) {
        console.log(e);
      }
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    const url = `${baseURL}${endpoint}`; // Ensure endpoint starts with '/'
    console.log(`API Call: ${options.method || 'GET'} ${url}`); // Log the call
    console.log(`API Call Headers: Authorization: Bearer ${token ? 'token-exists' : 'no-token'}`);

    try {
      console.log(`API Client: Sending fetch request to ${url}`);
      const response = await fetch(url, config);
      console.log(`API Client: Received response with status: ${response.status}`);
      
      if (!response.ok) {
        // Attempt to read error details from response body
        let errorDetail = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || JSON.stringify(errorData);
        } catch (e) {
          console.log(e);
        }
        console.error(`API Error: ${options.method || 'GET'} ${url} - Status ${response.status} - ${errorDetail}`);
        throw new ApiError(errorDetail, response.status, response);
      }
      
      return response; // Return the raw response for the caller to handle .json(), .text() etc.
    } catch (error) {
      console.error(`API Client: Fetch error for ${url}:`, error);
      throw error;
    }
  };
};

// Type for the returned API client function
export type ApiClient = ReturnType<typeof createApiClient>;

// Helper functions to work with the API client
export const fetchJson = async <T>(apiClient: ApiClient, endpoint: string, options: RequestInit = {}): Promise<T> => {
  const response = await apiClient(endpoint, options);
  return response.json() as Promise<T>;
};

// API Interface Types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  auth0_sub: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Club {
  id: string;
  name: string;
  description?: string;
  bank_account_balance: number;
  created_at: string;
  updated_at: string;
  memberships?: ClubMembership[];
  current_user_role?: string;
}

export interface ClubMembership {
  id: string;
  club_id: string;
  user_id: string;
  role: string;
  units: number;
  created_at: string;
  updated_at: string;
  user?: User;
}

export interface Fund {
  id: string;
  club_id: string;
  name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  brokerage_cash_balance: number;
}

export interface FundDetailed extends Fund {
  cash_balance: number;
  positions_market_value: number;
  total_value: number;
  percentage_of_club_assets: number;
}

export interface FundPerformancePoint {
  valuation_date: string;
  total_value: number;
}

export interface FundPerformanceHistory {
  history: FundPerformancePoint[];
}

export interface Asset {
  id: string;
  symbol: string;
  name: string;
  asset_type: string;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  fund_id: string;
  transaction_type: string;
  transaction_date: string;
  amount: number;
  quantity?: number;
  price_per_unit?: number;
  asset_id?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  asset?: Asset;
}

export interface MemberTransaction {
  id: string;
  membership_id: string;
  transaction_type: string;
  transaction_date: string;
  amount: number;
  units?: number;
  unit_value?: number;
  notes?: string;
  created_at: string;
  updated_at: string;
  membership?: ClubMembership;
}

export interface ClubPortfolio {
  club_id: string;
  valuation_date: string;
  total_value: number;
  cash_balance: number;
  positions: Position[];
}

export interface Position {
  asset_id: string;
  asset_symbol: string;
  asset_name: string;
  asset_type: string;
  quantity: number;
  current_price: number;
  market_value: number;
  cost_basis: number;
  unrealized_gain_loss: number;
  unrealized_gain_loss_percent: number;
}

export interface ActivityFeedItem {
  id: string;
  activity_date: string;
  item_type: string;
  description: string;
  amount?: number;
  user_name?: string;
  asset_symbol?: string;
  fund_name?: string;
}

// API Functions

// User API
export const getUserProfile = async (apiClient: ApiClient): Promise<User> => {
  return fetchJson<User>(apiClient, '/users/me');
};

// Clubs API
export const getUserClubs = async (apiClient: ApiClient): Promise<Club[]> => {
  return fetchJson<Club[]>(apiClient, '/clubs');
};

export const getClubDetails = async (apiClient: ApiClient, clubId: string): Promise<Club> => {
  return fetchJson<Club>(apiClient, `/clubs/${clubId}`);
};

export const createClub = async (apiClient: ApiClient, clubData: { name: string; description?: string }): Promise<Club> => {
  return fetchJson<Club>(apiClient, '/clubs', {
    method: 'POST',
    body: JSON.stringify(clubData),
  });
};

export const updateClub = async (apiClient: ApiClient, clubId: string, clubData: { name?: string; description?: string }): Promise<Club> => {
  return fetchJson<Club>(apiClient, `/clubs/${clubId}`, {
    method: 'PUT',
    body: JSON.stringify(clubData),
  });
};

export const getClubPortfolio = async (apiClient: ApiClient, clubId: string, valuationDate?: string): Promise<ClubPortfolio> => {
  const queryParams = valuationDate ? `?valuation_date=${valuationDate}` : '';
  return fetchJson<ClubPortfolio>(apiClient, `/clubs/${clubId}/portfolio${queryParams}`);
};

export interface UnitValueHistory {
  id: string;
  club_id: string;
  valuation_date: string;
  unit_value: number;
  total_units: number;
  total_value: number;
  created_at: string;
  updated_at: string;
}

export const calculateNav = async (apiClient: ApiClient, clubId: string, valuationDate: string): Promise<UnitValueHistory> => {
  return fetchJson<UnitValueHistory>(apiClient, `/clubs/${clubId}/calculate-nav`, {
    method: 'POST',
    body: JSON.stringify({ valuation_date: valuationDate }),
  });
};

// Club Members API
export const getClubMembers = async (apiClient: ApiClient, clubId: string): Promise<ClubMembership[]> => {
  return fetchJson<ClubMembership[]>(apiClient, `/clubs/${clubId}/members`);
};

export const addClubMember = async (apiClient: ApiClient, clubId: string, memberData: { member_email: string; role?: string }): Promise<ClubMembership> => {
  return fetchJson<ClubMembership>(apiClient, `/clubs/${clubId}/members`, {
    method: 'POST',
    body: JSON.stringify(memberData),
  });
};

export const updateMemberRole = async (apiClient: ApiClient, clubId: string, userId: string, newRole: string): Promise<ClubMembership> => {
  return fetchJson<ClubMembership>(apiClient, `/clubs/${clubId}/members/${userId}`, {
    method: 'PUT',
    body: JSON.stringify({ new_role: newRole }),
  });
};

export const removeMember = async (apiClient: ApiClient, clubId: string, userId: string): Promise<ClubMembership> => {
  return fetchJson<ClubMembership>(apiClient, `/clubs/${clubId}/members/${userId}`, {
    method: 'DELETE',
  });
};

// Member Transactions API
export const getMemberTransactions = async (apiClient: ApiClient, clubId: string, userId?: string): Promise<MemberTransaction[]> => {
  const queryParams = userId ? `?user_id=${userId}` : '';
  return fetchJson<MemberTransaction[]>(apiClient, `/clubs/${clubId}/member-transactions${queryParams}`);
};

export const recordMemberDeposit = async (apiClient: ApiClient, clubId: string, depositData: {
  user_id: string;
  amount: number;
  transaction_date?: string;
  notes?: string
}): Promise<MemberTransaction> => {
  return fetchJson<MemberTransaction>(apiClient, `/clubs/${clubId}/member-transactions/deposit`, {
    method: 'POST',
    body: JSON.stringify(depositData),
  });
};

export const recordMemberWithdrawal = async (apiClient: ApiClient, clubId: string, withdrawalData: {
  user_id: string;
  amount: number;
  transaction_date?: string;
  notes?: string
}): Promise<MemberTransaction> => {
  return fetchJson<MemberTransaction>(apiClient, `/clubs/${clubId}/member-transactions/withdrawal`, {
    method: 'POST',
    body: JSON.stringify(withdrawalData),
  });
};

export const getFundDetails = async (apiClient: ApiClient, clubId: string, fundId: string): Promise<FundDetailed> => {
  return fetchJson<FundDetailed>(apiClient, `/clubs/${clubId}/funds/${fundId}/details`);
};

export const getFundPerformanceHistory = async (
  apiClient: ApiClient,
  clubId: string,
  fundId: string,
  startDate?: string,
  endDate?: string
): Promise<FundPerformanceHistory> => {
  let queryParams = '';
  if (startDate) queryParams += `?start_date=${startDate}`;
  if (endDate) queryParams += queryParams ? `&end_date=${endDate}` : `?end_date=${endDate}`;
  
  return fetchJson<FundPerformanceHistory>(
    apiClient,
    `/clubs/${clubId}/funds/${fundId}/performance-history${queryParams}`
  );
};

// Funds API
export const getClubFunds = async (apiClient: ApiClient, clubId: string): Promise<Fund[]> => {
  return fetchJson<Fund[]>(apiClient, `/clubs/${clubId}/funds`);
};

export const updateFund = async (apiClient: ApiClient, clubId: string, fundId: string, fundData: {
  name?: string;
  description?: string;
  is_active?: boolean
}): Promise<Fund> => {
  return fetchJson<Fund>(apiClient, `/clubs/${clubId}/funds/${fundId}`, {
    method: 'PUT',
    body: JSON.stringify(fundData),
  });
};

export interface FundCreateData {
  name: string;
  description?: string;
}

export const createFund = async (apiClient: ApiClient, clubId: string, fundData: FundCreateData): Promise<Fund> => {
  return fetchJson<Fund>(apiClient, `/clubs/${clubId}/funds`, {
    method: 'POST',
    body: JSON.stringify(fundData),
  });
};

export interface FundSplit {
  id: string;
  club_id: string;
  fund_id: string;
  split_percentage: number;
  created_at: string;
  updated_at: string;
  fund?: Fund;
}

// Fund Splits API
export const getFundSplits = async (apiClient: ApiClient, clubId: string): Promise<FundSplit[]> => {
  return fetchJson<FundSplit[]>(apiClient, `/clubs/${clubId}/fund-splits`);
};

export const setFundSplits = async (apiClient: ApiClient, clubId: string, splits: { fund_id: string; split_percentage: number }[]): Promise<FundSplit[]> => {
  return fetchJson<FundSplit[]>(apiClient, `/clubs/${clubId}/fund-splits`, {
    method: 'PUT',
    body: JSON.stringify(splits),
  });
};

// Transactions API
export const getFundTransactions = async (apiClient: ApiClient, clubId: string, fundId?: string, assetId?: string): Promise<Transaction[]> => {
  let queryParams = '';
  if (fundId) queryParams += `?fund_id=${fundId}`;
  if (assetId) queryParams += queryParams ? `&asset_id=${assetId}` : `?asset_id=${assetId}`;
  
  return fetchJson<Transaction[]>(apiClient, `/clubs/${clubId}/transactions${queryParams}`);
};

export interface TradeData {
  fund_id: string;
  transaction_type: string; // 'BUY_STOCK' | 'SELL_STOCK' | 'BUY_OPTION' | 'SELL_OPTION'
  transaction_date: string;
  asset_id: string;
  quantity: number;
  price_per_unit: number;
  amount: number;
  notes?: string;
}

export const recordTrade = async (apiClient: ApiClient, clubId: string, tradeData: TradeData): Promise<Transaction> => {
  return fetchJson<Transaction>(apiClient, `/clubs/${clubId}/transactions/trade`, {
    method: 'POST',
    body: JSON.stringify(tradeData),
  });
};

export interface CashReceiptData {
  fund_id: string;
  transaction_type: string; // 'DIVIDEND' | 'INTEREST'
  transaction_date: string;
  amount: number;
  asset_id?: string;
  notes?: string;
}

export const recordCashReceipt = async (apiClient: ApiClient, clubId: string, receiptData: CashReceiptData): Promise<Transaction> => {
  return fetchJson<Transaction>(apiClient, `/clubs/${clubId}/transactions/cash-receipt`, {
    method: 'POST',
    body: JSON.stringify(receiptData),
  });
};

export interface CashTransferData {
  transaction_type: string; // 'BANK_TO_BROKERAGE' | 'BROKERAGE_TO_BANK' | 'INTERFUND_CASH_TRANSFER'
  transaction_date: string;
  total_amount: number; // Changed from 'amount' to 'total_amount' to match backend schema
  fund_id?: string; // Source fund for BROKERAGE_TO_BANK or INTERFUND_CASH_TRANSFER (source). Required for BANK_TO_BROKERAGE if not using fund_splits.
  target_fund_id?: string; // Target fund for INTERFUND_CASH_TRANSFER
  notes?: string;
  use_fund_splits?: boolean; // For BANK_TO_BROKERAGE, whether to use the club's fund splits
}

export const recordCashTransfer = async (apiClient: ApiClient, clubId: string, transferData: CashTransferData): Promise<Transaction | Transaction[]> => {
  return fetchJson<Transaction | Transaction[]>(apiClient, `/clubs/${clubId}/transactions/cash-transfer`, {
    method: 'POST',
    body: JSON.stringify(transferData),
  });
};

export interface OptionLifecycleData {
  fund_id: string;
  transaction_type: string; // 'OPTION_EXERCISE' | 'OPTION_ASSIGNMENT' | 'OPTION_EXPIRATION'
  transaction_date: string;
  asset_id: string;
  quantity: number;
  amount?: number;
  notes?: string;
}

export const recordOptionLifecycle = async (apiClient: ApiClient, clubId: string, lifecycleData: OptionLifecycleData): Promise<Transaction> => {
  return fetchJson<Transaction>(apiClient, `/clubs/${clubId}/transactions/option-lifecycle`, {
    method: 'POST',
    body: JSON.stringify(lifecycleData),
  });
};

// Assets API
export const getAssets = async (apiClient: ApiClient): Promise<Asset[]> => {
  return fetchJson<Asset[]>(apiClient, '/assets');
};

export const getAssetById = async (apiClient: ApiClient, assetId: string): Promise<Asset> => {
  return fetchJson<Asset>(apiClient, `/assets/${assetId}`);
};

export const getOrCreateStockAsset = async (apiClient: ApiClient, stockData: {
  symbol: string;
  name?: string
}): Promise<Asset> => {
  return fetchJson<Asset>(apiClient, '/assets/stock', {
    method: 'POST',
    body: JSON.stringify(stockData),
  });
};

export const getClubActivityFeed = async (apiClient: ApiClient, clubId: string, limit: number = 10): Promise<ActivityFeedItem[]> => {
  return fetchJson<ActivityFeedItem[]>(apiClient, `/clubs/${clubId}/activity-feed?limit=${limit}`);
};

export interface OptionAssetData {
  underlying_symbol: string;
  option_type: string; // 'CALL' | 'PUT'
  strike_price: number;
  expiration_date: string;
  contract_size?: number;
}

export const getOrCreateOptionAsset = async (apiClient: ApiClient, optionData: OptionAssetData): Promise<Asset> => {
  return fetchJson<Asset>(apiClient, '/assets/option', {
    method: 'POST',
    body: JSON.stringify(optionData),
  });
};

export interface ClubExpenseData {
  transaction_type: string; // 'CLUB_EXPENSE'
  transaction_date: string;
  total_amount: number;
  fees_commissions?: number;
  description?: string;
}

export const recordClubExpense = async (apiClient: ApiClient, clubId: string, expenseData: ClubExpenseData): Promise<Transaction> => {
  return fetchJson<Transaction>(apiClient, `/clubs/${clubId}/transactions/club-expense`, {
    method: 'POST',
    body: JSON.stringify(expenseData),
  });
};