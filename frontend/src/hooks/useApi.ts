// src/hooks/useApi.ts
import { useAuth0 } from '@auth0/auth0-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { UseMutationOptions, UseQueryOptions, UseQueryResult } from '@tanstack/react-query';
import {
  createApiClient,
  ApiError,
  
  // User API
  getUserProfile,
  
  // Clubs API
  getUserClubs,
  getClubDetails,
  createClub,
  updateClub,
  getClubPortfolio,
  calculateNav,
  
  // Club Members API
  getClubMembers,
  addClubMember,
  updateMemberRole,
  removeMember,
  
  // Member Transactions API
  getMemberTransactions,
  recordMemberDeposit,
  recordMemberWithdrawal,
  
  // Funds API
  getClubFunds,
  createFund,
  updateFund,
  getFundDetails,
  getFundPerformanceHistory,
  
  // Fund Splits API
  getFundSplits,
  setFundSplits,
  
  // Transactions API
  getFundTransactions,
  recordTrade,
  recordCashReceipt,
  recordCashTransfer,
  recordOptionLifecycle,
  recordClubExpense,
  getClubActivityFeed,
  
  // Assets API
  getAssets,
  getAssetById,
  getOrCreateStockAsset,
  getOrCreateOptionAsset,
} from '@/lib/apiClient';

import type {
  ApiClient,
  User,
  Club,
  ClubPortfolio,
  UnitValueHistory,
  ClubMembership,
  MemberTransaction,
  Fund,
  FundDetailed,
  FundPerformanceHistory,
  FundSplit,
  Transaction,
  TradeData,
  CashReceiptData,
  CashTransferData,
  OptionLifecycleData,
  ClubExpenseData,
  Asset,
  OptionAssetData,
  FundCreateData,
  ActivityFeedItem
} from '@/lib/apiClient';

// Create a hook to get the API client
export const useApiClient = (): ApiClient => {
  const { getAccessTokenSilently } = useAuth0();
  return createApiClient(getAccessTokenSilently);
};

// User Hooks
export const useUserProfile = (options?: UseQueryOptions<User, ApiError>) => {
  const apiClient = useApiClient();
  
  return useQuery<User, ApiError>({
    queryKey: ['user', 'profile'],
    queryFn: () => getUserProfile(apiClient),
    ...options
  });
};

// Clubs Hooks
export const useUserClubs = (options?: UseQueryOptions<Club[], ApiError>) => {
  const apiClient = useApiClient();
  
  return useQuery<Club[], ApiError>({
    queryKey: ['clubs'],
    queryFn: () => getUserClubs(apiClient),
    ...options
  });
};

export const useClubDetails = (clubId: string, options?: UseQueryOptions<Club, ApiError>) => {
  const apiClient = useApiClient();
  
  return useQuery<Club, ApiError>({
    queryKey: ['clubs', clubId],
    queryFn: () => getClubDetails(apiClient, clubId),
    enabled: !!clubId,
    ...options
  });
};

export const useCreateClub = (options?: UseMutationOptions<Club, ApiError, { name: string; description?: string }>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<Club, ApiError, { name: string; description?: string }>({
    mutationFn: (clubData) => createClub(apiClient, clubData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clubs'] });
    },
    ...options
  });
};

export const useUpdateClub = (clubId: string, options?: UseMutationOptions<Club, ApiError, { name?: string; description?: string }>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<Club, ApiError, { name?: string; description?: string }>({
    mutationFn: (clubData) => updateClub(apiClient, clubId, clubData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId] });
      queryClient.invalidateQueries({ queryKey: ['clubs'] });
    },
    ...options
  });
};

export const useClubPortfolio = (clubId: string, valuationDate?: string, options?: UseQueryOptions<ClubPortfolio, ApiError>) => {
  const apiClient = useApiClient();
  
  return useQuery<ClubPortfolio, ApiError>({
    queryKey: ['clubs', clubId, 'portfolio', valuationDate],
    queryFn: () => getClubPortfolio(apiClient, clubId, valuationDate),
    enabled: !!clubId,
    ...options
  });
};

export const useCalculateNav = (clubId: string, options?: UseMutationOptions<UnitValueHistory, ApiError, string>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<UnitValueHistory, ApiError, string>({
    mutationFn: (valuationDate) => calculateNav(apiClient, clubId, valuationDate),
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'portfolio'] });
    },
    ...options
  });
};

// Club Members Hooks
export const useClubMembers = (clubId: string, options?: UseQueryOptions<ClubMembership[], ApiError>) => {
  const apiClient = useApiClient();
  
  return useQuery<ClubMembership[], ApiError>({
    queryKey: ['clubs', clubId, 'members'],
    queryFn: () => getClubMembers(apiClient, clubId),
    enabled: !!clubId,
    ...options
  });
};

export const useAddClubMember = (clubId: string, options?: UseMutationOptions<ClubMembership, ApiError, { member_email: string; role?: string }>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<ClubMembership, ApiError, { member_email: string; role?: string }>({
    mutationFn: (memberData) => addClubMember(apiClient, clubId, memberData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'members'] });
    },
    ...options
  });
};

export const useUpdateMemberRole = (clubId: string, options?: UseMutationOptions<ClubMembership, ApiError, { userId: string; newRole: string }>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<ClubMembership, ApiError, { userId: string; newRole: string }>({
    mutationFn: ({ userId, newRole }) => updateMemberRole(apiClient, clubId, userId, newRole),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'members'] });
    },
    ...options
  });
};

export const useRemoveMember = (clubId: string, options?: UseMutationOptions<ClubMembership, ApiError, string>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<ClubMembership, ApiError, string>({
    mutationFn: (userId) => removeMember(apiClient, clubId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'members'] });
    },
    ...options
  });
};

// Member Transactions Hooks
export const useMemberTransactions = (clubId: string, userId?: string, options?: UseQueryOptions<MemberTransaction[], ApiError>) => {
  const apiClient = useApiClient();
  
  return useQuery<MemberTransaction[], ApiError>({
    queryKey: ['clubs', clubId, 'member-transactions', userId],
    queryFn: () => getMemberTransactions(apiClient, clubId, userId),
    enabled: !!clubId,
    ...options
  });
};

export const useRecordMemberDeposit = (clubId: string, options?: UseMutationOptions<MemberTransaction, ApiError, { 
  user_id: string; 
  amount: number; 
  transaction_date?: string; 
  notes?: string 
}>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<MemberTransaction, ApiError, { 
    user_id: string; 
    amount: number; 
    transaction_date?: string; 
    notes?: string 
  }>({
    mutationFn: (depositData) => recordMemberDeposit(apiClient, clubId, depositData),
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'member-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId] }); // Invalidate club details to refresh bank_account_balance
    },
    ...options
  });
};

export const useRecordMemberWithdrawal = (clubId: string, options?: UseMutationOptions<MemberTransaction, ApiError, { 
  user_id: string; 
  amount: number; 
  transaction_date?: string; 
  notes?: string 
}>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<MemberTransaction, ApiError, { 
    user_id: string; 
    amount: number; 
    transaction_date?: string; 
    notes?: string 
  }>({
    mutationFn: (withdrawalData) => recordMemberWithdrawal(apiClient, clubId, withdrawalData),
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'member-transactions'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId] }); // Invalidate club details to refresh bank_account_balance
    },
    ...options
  });
};

// Funds Hooks
export const useClubFunds = (clubId: string, options?: UseQueryOptions<Fund[], ApiError>) => {
  const apiClient = useApiClient();
  
  return useQuery<Fund[], ApiError>({
    queryKey: ['clubs', clubId, 'funds'],
    queryFn: () => getClubFunds(apiClient, clubId),
    enabled: !!clubId,
    ...options
  });
};

export const useCreateClubFund = (clubId: string, options?: UseMutationOptions<Fund, ApiError, FundCreateData>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<Fund, ApiError, FundCreateData>({
    mutationFn: (fundData) => createFund(apiClient, clubId, fundData),
    onSuccess: () => {
      // Invalidate and refetch relevant queries
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'funds'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'portfolio'] });
    },
    ...options
  });
};

export const useUpdateFund = (clubId: string, options?: UseMutationOptions<Fund, ApiError, { 
  fundId: string; 
  fundData: { 
    name?: string; 
    description?: string; 
    is_active?: boolean 
  } 
}>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<Fund, ApiError, { 
    fundId: string; 
    fundData: { 
      name?: string; 
      description?: string; 
      is_active?: boolean 
    } 
  }>({
    mutationFn: ({ fundId, fundData }) => updateFund(apiClient, clubId, fundId, fundData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'funds'] });
    },
    ...options
  });
};

export const useFundDetails = (clubId: string, fundId: string, options?: UseQueryOptions<FundDetailed, ApiError>) => {
  const apiClient = useApiClient();
  
  return useQuery<FundDetailed, ApiError>({
    queryKey: ['clubs', clubId, 'funds', fundId, 'details'],
    queryFn: () => getFundDetails(apiClient, clubId, fundId),
    enabled: !!clubId && !!fundId,
    ...options
  });
};

export const useFundPerformanceHistory = (
  clubId: string,
  fundId: string,
  startDate?: string,
  endDate?: string,
  options?: UseQueryOptions<FundPerformanceHistory, ApiError>
) => {
  const apiClient = useApiClient();
  
  return useQuery<FundPerformanceHistory, ApiError>({
    queryKey: ['clubs', clubId, 'funds', fundId, 'performance-history', startDate, endDate],
    queryFn: () => getFundPerformanceHistory(apiClient, clubId, fundId, startDate, endDate),
    enabled: !!clubId && !!fundId,
    ...options
  });
};

// Fund Splits Hooks
export const useFundSplits = (clubId: string, options?: UseQueryOptions<FundSplit[], ApiError>) => {
  const apiClient = useApiClient();
  
  return useQuery<FundSplit[], ApiError>({
    queryKey: ['clubs', clubId, 'fund-splits'],
    queryFn: () => getFundSplits(apiClient, clubId),
    enabled: !!clubId,
    ...options
  });
};

export const useSetFundSplits = (clubId: string, options?: UseMutationOptions<FundSplit[], ApiError, { fund_id: string; split_percentage: number }[]>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<FundSplit[], ApiError, { fund_id: string; split_percentage: number }[]>({
    mutationFn: (splits) => setFundSplits(apiClient, clubId, splits),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'fund-splits'] });
    },
    ...options
  });
};

// Transactions Hooks
export const useFundTransactions = (clubId: string, fundId?: string, assetId?: string, options?: UseQueryOptions<Transaction[], ApiError>) => {
  const apiClient = useApiClient();
  
  return useQuery<Transaction[], ApiError>({
    queryKey: ['clubs', clubId, 'transactions', fundId, assetId],
    queryFn: () => getFundTransactions(apiClient, clubId, fundId, assetId),
    enabled: !!clubId,
    ...options
  });
};

export const useRecordTrade = (clubId: string, options?: UseMutationOptions<Transaction, ApiError, TradeData>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<Transaction, ApiError, TradeData>({
    mutationFn: (tradeData) => recordTrade(apiClient, clubId, tradeData),
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'portfolio'] });
    },
    ...options
  });
};

export const useRecordCashReceipt = (clubId: string, options?: UseMutationOptions<Transaction, ApiError, CashReceiptData>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<Transaction, ApiError, CashReceiptData>({
    mutationFn: (receiptData) => recordCashReceipt(apiClient, clubId, receiptData),
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId] }); // Invalidate club details to refresh bank_account_balance
    },
    ...options
  });
};

export const useRecordCashTransfer = (clubId: string, options?: UseMutationOptions<Transaction | Transaction[], ApiError, CashTransferData>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<Transaction | Transaction[], ApiError, CashTransferData>({
    mutationFn: (transferData) => recordCashTransfer(apiClient, clubId, transferData),
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'funds'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId] });
    },
    ...options
  });
};

export const useRecordOptionLifecycle = (clubId: string, options?: UseMutationOptions<Transaction, ApiError, OptionLifecycleData>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<Transaction, ApiError, OptionLifecycleData>({
    mutationFn: (lifecycleData) => recordOptionLifecycle(apiClient, clubId, lifecycleData),
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'portfolio'] });
    },
    ...options
  });
};

export const useRecordClubExpense = (clubId: string, options?: UseMutationOptions<Transaction, ApiError, ClubExpenseData>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<Transaction, ApiError, ClubExpenseData>({
    mutationFn: (expenseData) => recordClubExpense(apiClient, clubId, expenseData),
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'transactions'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['clubs', clubId] }); // Correct query key for club details
    },
    ...options
  });
};

// Assets Hooks
export const useAssets = (options?: UseQueryOptions<Asset[], ApiError>) => {
  const apiClient = useApiClient();
  
  return useQuery<Asset[], ApiError>({
    queryKey: ['assets'],
    queryFn: () => getAssets(apiClient),
    ...options
  });
};

export const useAssetById = (assetId: string, options?: UseQueryOptions<Asset, ApiError>) => {
  const apiClient = useApiClient();
  
  return useQuery<Asset, ApiError>({
    queryKey: ['assets', assetId],
    queryFn: () => getAssetById(apiClient, assetId),
    enabled: !!assetId,
    ...options
  });
};

export const useGetOrCreateStockAsset = (options?: UseMutationOptions<Asset, ApiError, { symbol: string; name?: string }>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<Asset, ApiError, { symbol: string; name?: string }>({
    mutationFn: (stockData) => getOrCreateStockAsset(apiClient, stockData),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.setQueryData(['assets', data.id], data);
    },
    ...options
  });
};

export const useGetOrCreateOptionAsset = (options?: UseMutationOptions<Asset, ApiError, OptionAssetData>) => {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  
  return useMutation<Asset, ApiError, OptionAssetData>({
    mutationFn: (optionData) => getOrCreateOptionAsset(apiClient, optionData),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      queryClient.setQueryData(['assets', data.id], data);
    },
    ...options
  });
};

// Hook to fetch activity feed for a club (for dashboard activity feed)
export interface TransactionRead {
  id: string;
  fund_id?: string;
  asset_id?: string;
  transaction_type: string;
  transaction_date: string;
  quantity?: number;
  price_per_unit?: number;
  total_amount: number;
  description?: string;
  created_at: string;
  updated_at: string;
  asset?: {
    id: string;
    symbol: string;
    name: string;
    asset_type: string;
  };
}

export const useClubActivityFeed = (
  clubId: string,
  limit: number = 10
): UseQueryResult<ActivityFeedItem[], ApiError> => {
  const apiClient = useApiClient();
  
  return useQuery<ActivityFeedItem[], ApiError>({
    queryKey: ['clubActivityFeed', clubId, limit],
    queryFn: () => getClubActivityFeed(apiClient, clubId, limit),
    enabled: !!clubId,
  });
};

// Keep the old hook for backward compatibility, but it now uses the new endpoint
export const useClubRecentActivity = (clubId: string | undefined, limit: number = 5) => {
  return useClubActivityFeed(clubId || '', limit);
};