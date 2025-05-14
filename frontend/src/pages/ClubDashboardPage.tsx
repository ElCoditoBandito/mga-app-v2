// frontend/src/pages/ClubDashboardPage.tsx
import React, { useState, useMemo } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useAuth0 } from '@auth0/auth0-react';
import { cn } from '@/lib/utils';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import LogClubExpenseForm from '@/components/forms/LogClubExpenseForm';
import type { ClubExpenseFormData } from '@/components/forms/LogClubExpenseForm';
import RecordMemberTransactionForm from '@/components/forms/RecordMemberTransactionForm';
import type { MemberTransactionFormData } from '@/components/forms/RecordMemberTransactionForm';
import LogCashTransferForm from '@/components/forms/LogCashTransferForm';
import type { CashTransferFormData } from '@/components/forms/LogCashTransferForm';
import {
  DollarSign,
  TrendingUp,
  Users,
  BookOpen,
  Banknote,
  ClipboardPlus,
  RefreshCw,
  ArrowRightLeft,
  Activity,
  ArrowUpCircle,
  ArrowDownCircle
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  // Legend, // Legend might not be needed for a single line chart
} from 'recharts';

// Import our custom hooks
import {
  useClubDetails,
  useClubPortfolio,
  useClubMembers,
  useCalculateNav,
  useRecordMemberDeposit,
  useRecordMemberWithdrawal,
  useRecordCashTransfer,
  useClubFunds,
  useRecordClubExpense,
  useClubActivityFeed
} from '@/hooks/useApi';

// Import types and enums
import type {
  ClubPortfolio as ClubPortfolioType,
  ActivityFeedItem
} from '@/lib/apiClient';
import { MemberTransactionType, TransactionType } from '@/enums';

// TypeScript interfaces for dashboard data
export interface PerformanceDataPoint {
  date: string;
  totalClubValue: number;
}

export interface KeyMetrics {
  totalClubValue: number;
  valuationDate: string;
  previousClubValue: number;
  currentUnitValue: number;
  totalUnitsOutstanding: number;
  clubBankBalance: number;
  totalBrokerageCash: number;
  membersCount: number;
}

export interface FundSummary {
  fundId: string;
  fundName: string;
  fundValue?: number;
  brokerageCash?: number;
  percentageOfClub?: number;
  investmentStyle: string;
}

export interface RecentActivityItem {
  id: string;
  date: string;
  type: string;
  description: string;
  amount: number;
  link: string;
  member?: string;
  fund?: string;
}

export interface ClubDashboardData {
  clubId: string;
  clubName: string;
  keyMetrics: KeyMetrics;
  performanceChartData: PerformanceDataPoint[];
  isAdmin: boolean;
  fundSummaries: FundSummary[];
  recentActivity: RecentActivityItem[];
}

// Helper function to transform portfolio data into performance data points
const transformPortfolioToPerformanceData = (portfolio: ClubPortfolioType): PerformanceDataPoint[] => {
  // In a real implementation, this would use historical data from the API
  // For now, we'll create a single data point from the current portfolio
  return [
    {
      date: portfolio.valuation_date,
      totalClubValue: portfolio.total_value
    }
  ];
};

// Helper function to create a recent activity item
// This is used in the recentActivity useMemo hook

const formatCurrency = (value?: number | null, withSign = false) => {
  if (value == null) return 'N/A';
  const options = { style: 'currency', currency: 'USD' } as Intl.NumberFormatOptions;
  if (withSign) options.signDisplay = 'always';
  return new Intl.NumberFormat('en-US', options).format(value);
};

const formatNumber = (value?: number | null) => {
  if (value == null) return 'N/A';
  return new Intl.NumberFormat('en-US').format(value);
};

const formatDate = (dateInput?: string | number | Date) => {
  if (!dateInput) return 'N/A';
  return new Date(dateInput).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric'
  });
};

const formatShortDate = (dateInput?: string | number | Date) => {
  if (!dateInput) return 'N/A';
  return new Date(dateInput).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric'
  });
};

interface MetricCardProps {
  title: string; value: string; subtext?: string; icon: React.ElementType; trend?: 'up' | 'down' | 'neutral'; className?: string;
}

const MetricCard = ({ title, value, subtext, icon: Icon, trend, className }: MetricCardProps) => (
  <Card className={cn('bg-white border-slate-200/75 shadow-sm hover:shadow-md transition-all', className)}>
    <CardHeader className="pb-2">
      <CardTitle className="text-[0.7rem] font-medium text-slate-500 uppercase tracking-wider flex justify-between items-center">
        {title} <Icon className="h-4 w-4 text-slate-400" />
      </CardTitle>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      {subtext && <p className="text-xs text-slate-500">{subtext}</p>}
      {trend && trend !== 'neutral' && (
        <div className={cn('text-xs font-medium flex items-center mt-1', trend === 'up' ? 'text-green-500' : 'text-red-500')}>
          {trend === 'up' ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingUp className="h-3 w-3 mr-1 transform scale-y-[-1]" />}
        </div>
      )}
    </CardContent>
  </Card>
);

interface TooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
  }>;
  label?: string | number;
}

const CustomTooltip = ({ active, payload, label }: TooltipProps) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 shadow-lg rounded-lg border border-slate-200">
        <p className="text-xs text-slate-500">{formatDate(label)}</p>
        <p className="text-sm font-medium text-slate-800">
          {`${payload[0].name}: `}
          <span className="text-blue-600 font-bold">{formatCurrency(payload[0].value)}</span>
        </p>
      </div>
    );
  }
  return null;
};

// Type assertion for recharts components to fix TypeScript errors

const ClubDashboardPage = () => {
  const { clubId } = useParams<{ clubId: string }>();
  const queryClient = useQueryClient();
  const [timeRange, setTimeRange] = useState('YTD');
  
  // Modal states for forms
  const [expenseModalOpen, setExpenseModalOpen] = useState(false);
  const [memberTxModalOpen, setMemberTxModalOpen] = useState(false);
  const [cashTransferModalOpen, setCashTransferModalOpen] = useState(false);
  
  // Auth0 hook to get user info
  const { user } = useAuth0();
  
  // React Query hooks
  const {
    isLoading: isLoadingClubDetails,
    error: clubDetailsError
  } = useClubDetails(clubId || '');
  
  const {
    data: clubPortfolio,
    isLoading: isLoadingPortfolio,
    error: portfolioError
  } = useClubPortfolio(clubId || '');
  
  const {
    data: clubMembers,
    isLoading: isLoadingMembers
  } = useClubMembers(clubId || '');
  
  const {
    data: actualFunds = [],
    isLoading: isLoadingActualFunds,
    error: actualFundsError
  } = useClubFunds(clubId || '');
  
  const { data: rawRecentTransactions = [] } = useClubActivityFeed(clubId || '', 5);
  
  const {
    mutate: calculateNav,
    isPending: isRecalculating
  } = useCalculateNav(clubId || '');
  
  const { mutate: recordDeposit } = useRecordMemberDeposit(clubId || '');
  const { mutate: recordWithdrawal } = useRecordMemberWithdrawal(clubId || '');
  const { mutate: recordCashTransfer } = useRecordCashTransfer(clubId || '');
  const { mutate: recordExpense, isPending: isRecordingExpense } = useRecordClubExpense(clubId || '');
  
  // Combine loading states
  const isLoading = isLoadingClubDetails || isLoadingPortfolio || isLoadingMembers || isLoadingActualFunds;
  
  // Combine error states
  const error = clubDetailsError || portfolioError || actualFundsError;

  // Move all useMemo hooks before any conditional returns
  // Extract key metrics from portfolio data
  const keyMetrics = useMemo(() => {
    if (!clubPortfolio || !clubMembers) {
      return {
        totalClubValue: 0,
        valuationDate: new Date().toISOString().split('T')[0],
        previousClubValue: 0,
        currentUnitValue: 0,
        totalUnitsOutstanding: 0,
        clubBankBalance: 0,
        totalBrokerageCash: 0,
        membersCount: 0
      };
    }
    
    // In a real implementation, we would get previous club value from historical data
    // For now, we'll just use a slightly lower value
    const previousClubValue = clubPortfolio.total_value * 0.995;
    
    // Calculate total units outstanding
    const totalUnits = clubMembers.reduce((sum, member) => sum + (member.units || 0), 0);
    
    // Calculate unit value
    const unitValue = totalUnits > 0 ? clubPortfolio.total_value / totalUnits : 0;
    
    // Calculate total brokerage cash from positions
    const totalBrokerageCash = clubPortfolio.cash_balance;
    
    return {
      totalClubValue: clubPortfolio.total_value,
      valuationDate: clubPortfolio.valuation_date,
      previousClubValue,
      currentUnitValue: unitValue,
      totalUnitsOutstanding: totalUnits,
      clubBankBalance: 0, // This would come from a different API endpoint
      totalBrokerageCash,
      membersCount: clubMembers.length
    };
  }, [clubPortfolio, clubMembers]);
  
  // Extract fund summaries from actual funds data
  const fundSummaries = useMemo(() => {
    if (!actualFunds || actualFunds.length === 0) return [];
    
    return actualFunds
      .filter(fund => fund.is_active)
      .map(fund => ({
        fundId: fund.id,
        fundName: fund.name,
        // For MVP, fundValue, brokerageCash, percentageOfClub will be undefined
        // and rely on formatCurrency to show "N/A"
        fundValue: undefined,
        brokerageCash: undefined,
        percentageOfClub: undefined,
        investmentStyle: fund.description || 'No specific investment style described.'
      }));
  }, [actualFunds]);
  
  // Create recent activity items
  const recentActivity = useMemo((): RecentActivityItem[] => {
    // Ensure rawRecentTransactions is used from the useClubActivityFeed hook
    if (!rawRecentTransactions || rawRecentTransactions.length === 0) {
      return [];
    }

    return rawRecentTransactions.map((item: ActivityFeedItem): RecentActivityItem => {
      let displayType = item.item_type; // Default to item_type
      let description = item.description || '';
      // Ensure amount is treated as a string before parseFloat, and default to '0' if null/undefined
      const amount = parseFloat(item.amount?.toString() || '0');
      let link = `/club/${clubId}/transactions`; // Generic link
      const fundName = item.fund_name || 'Club Account';
      const userName = item.user_name;

      // Simplify the display type based on item_type
      switch (item.item_type) {
        case TransactionType.BUY_STOCK:
          displayType = 'Buy Stock';
          link = item.asset_symbol ? `/club/${clubId}/assets/${item.asset_symbol}` : link;
          break;
        case TransactionType.SELL_STOCK:
          displayType = 'Sell Stock';
          link = item.asset_symbol ? `/club/${clubId}/assets/${item.asset_symbol}` : link;
          break;
        case TransactionType.BUY_OPTION:
          displayType = 'Buy Option';
          link = item.asset_symbol ? `/club/${clubId}/assets/${item.asset_symbol}` : link;
          break;
        case TransactionType.SELL_OPTION:
          displayType = 'Sell Option';
          link = item.asset_symbol ? `/club/${clubId}/assets/${item.asset_symbol}` : link;
          break;
        case TransactionType.DIVIDEND:
          displayType = 'Dividend';
          link = item.asset_symbol ? `/club/${clubId}/assets/${item.asset_symbol}` : link;
          break;
        case TransactionType.BROKERAGE_INTEREST:
          displayType = 'Brokerage Interest';
          break;
        case TransactionType.CLUB_EXPENSE:
          displayType = 'Club Expense';
          break;
        case TransactionType.BANK_TO_BROKERAGE:
          displayType = 'Transfer to Brokerage';
          break;
        case TransactionType.BROKERAGE_TO_BANK:
          displayType = 'Transfer to Bank';
          break;
        case MemberTransactionType.DEPOSIT:
          displayType = 'Member Deposit';
          break;
        case MemberTransactionType.WITHDRAWAL:
          displayType = 'Member Withdrawal';
          break;
        default:
          // Keep original description if present, otherwise use item_type
          description = description || `Activity: ${item.item_type}`;
      }

      return {
        id: item.id,
        date: item.activity_date,
        type: displayType,
        description: description,
        amount: amount,
        link: link,
        fund: fundName !== 'Club Account' ? fundName : undefined,
        member: userName
      };
    });
  }, [rawRecentTransactions, clubId]); // Ensure dependencies are rawRecentTransactions and clubId
  
  // Transform portfolio data into performance data points
  const performanceData = useMemo(() => {
    if (!clubPortfolio) return [];
    return transformPortfolioToPerformanceData(clubPortfolio);
  }, [clubPortfolio]);
  
  // Convert performance data to chart format
  const allChartData = useMemo(() => {
    return performanceData.map((d) => ({
      ...d,
      date: new Date(d.date).getTime(), // Convert to timestamp for easier filtering
    })).sort((a, b) => a.date - b.date) || []; // Ensure data is sorted by date
  }, [performanceData]);

  const filteredChartData = useMemo(() => {
    if (!allChartData.length) return [];
    const now = new Date(clubPortfolio?.valuation_date || Date.now()); // Use valuationDate as 'today' for consistency
    let startDate = new Date(allChartData[0].date); // Default to all data

    switch (timeRange) {
      case '1M':
        startDate = new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
        break;
      case '3M':
        startDate = new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
        break;
      case '6M':
        startDate = new Date(now.getFullYear(), now.getMonth() - 6, now.getDate());
        break;
      case 'YTD':
        startDate = new Date(now.getFullYear(), 0, 1);
        break;
      case '1Y':
        startDate = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
        break;
      case 'All':
      default:
        // startDate remains the earliest date in the dataset
        return allChartData;
    }
    
    const startTime = startDate.getTime();
    // Ensure the latest point (now) is included if it falls within the general range but might be missed by exact start date match
    return allChartData.filter((d) => d.date >= startTime && d.date <= now.getTime());

  }, [allChartData, timeRange, clubPortfolio?.valuation_date]);

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        {/* Skeleton for Key Metrics Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-6 gap-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-[120px] w-full rounded-lg" />
          ))}
        </div>
        
        {/* Skeleton for Chart */}
        <Skeleton className="h-[400px] w-full rounded-lg" />
        
        {/* Skeleton for Fund Overview and Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Skeleton className="h-[300px] w-full rounded-lg" />
            <Skeleton className="h-[200px] w-full rounded-lg" />
          </div>
          <div className="lg:col-span-1">
            <Skeleton className="h-[400px] w-full rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  // Determine if user is admin
  const isAdmin = clubMembers?.some(member =>
    member.user_id === user?.sub && member.role === 'ADMIN'
  ) || false;
  
  // Calculate club value trend
  const clubValueTrend = keyMetrics.totalClubValue > keyMetrics.previousClubValue ? 'up' :
                         (keyMetrics.totalClubValue < keyMetrics.previousClubValue ? 'down' : 'neutral');

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-red-50 border border-red-200 rounded-lg">
        <div className="text-red-500 mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-red-700 mb-2">Unable to Load Dashboard Data</h3>
        <p className="text-red-600 text-center mb-4">
          {"There was a problem retrieving the club dashboard data. Please try again later."}
        </p>
        <Button variant="outline" className="bg-white border-red-300 text-red-700 hover:bg-red-50">
          Retry
        </Button>
      </div>
    );
  }

  // Time range buttons for chart
  const timeRangeButtons = [
    { label: '1M', value: '1M' }, { label: '3M', value: '3M' }, { label: '6M', value: '6M' },
    { label: 'YTD', value: 'YTD' }, { label: '1Y', value: '1Y' }, { label: 'All', value: 'All' },
  ];


  // Handler for recalculate button
  function handleRecalculate() {
    if (!clubId) return;
    
    toast.info('Starting club valuation recalculation...');
    
    // Get today's date in YYYY-MM-DD format
    const today = new Date().toISOString().split('T')[0];
    
    // Call the mutation
    calculateNav(today, {
      onSuccess: () => {
        toast.success('Club valuation recalculated successfully');
      },
      onError: (error) => {
        console.error('Error recalculating club valuation:', error);
        toast.error('Failed to recalculate club valuation');
      }
    });
  }

  // Handler for expense form submission
  function handleExpenseSubmit(formData: ClubExpenseFormData) {
    console.log('Submitting expense:', formData);
    
    // Create expense payload
    const expensePayload = {
      transaction_type: 'CLUB_EXPENSE',
      transaction_date: formData.transaction_date,
      total_amount: formData.total_amount,
      fees_commissions: formData.fees_commissions || 0,
      description: formData.description
    };
    
    // Record the expense
    recordExpense(expensePayload, {
      onSuccess: () => {
        toast.success('Club expense logged successfully');
        setExpenseModalOpen(false);
      },
      onError: (error) => {
        console.error('Error logging club expense:', error);
        toast.error(`Failed to log club expense: ${error.message}`);
      }
    });
  }

  // Handler for member transaction form submission
  function handleMemberTxSubmit(formData: MemberTransactionFormData) {
    console.log('Submitting member transaction:', formData);
    
    // Determine if it's a deposit or withdrawal
    if (formData.transaction_type === MemberTransactionType.DEPOSIT) {
      recordDeposit({
        user_id: formData.user_id,
        amount: formData.amount,
        transaction_date: formData.transaction_date,
        notes: formData.notes
      }, {
        onSuccess: () => {
          toast.success('Member deposit recorded successfully');
          setMemberTxModalOpen(false);
        },
        onError: (error) => {
          console.error('Error recording member deposit:', error);
          toast.error('Failed to record member deposit');
        }
      });
    } else {
      recordWithdrawal({
        user_id: formData.user_id,
        amount: formData.amount,
        transaction_date: formData.transaction_date,
        notes: formData.notes
      }, {
        onSuccess: () => {
          toast.success('Member withdrawal recorded successfully');
          setMemberTxModalOpen(false);
        },
        onError: (error) => {
          console.error('Error recording member withdrawal:', error);
          toast.error('Failed to record member withdrawal');
        }
      });
    }
  }

  // Define an interface for the cash transfer payload
  interface CashTransferPayload {
    transaction_type: string;
    transaction_date: string;
    total_amount: number;
    fund_id?: string;
    target_fund_id?: string;
    notes?: string;
  }

  // Handler for cash transfer form submission
  function handleCashTransferSubmit(formData: CashTransferFormData) {
    console.log('Submitting cash transfer:', formData);
    
    // Create the payload for recordCashTransfer
    const payload: CashTransferPayload = {
      transaction_type: formData.transaction_type,
      transaction_date: formData.transaction_date,
      total_amount: formData.total_amount
    };
    
    // Add optional fields only if they are defined
    if (formData.fund_id !== undefined) {
      payload.fund_id = formData.fund_id;
    }
    
    if (formData.target_fund_id !== undefined) {
      payload.target_fund_id = formData.target_fund_id;
    }
    
    if (formData.description !== undefined) {
      payload.notes = formData.description; // Map description to notes
    }
    
    recordCashTransfer(payload, {
      onSuccess: () => {
        toast.success('Cash transfer logged successfully!');
        setCashTransferModalOpen(false);
        // Invalidate queries that might be affected by this cash transfer
        queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'portfolio'] });
        queryClient.invalidateQueries({ queryKey: ['clubs', clubId, 'funds'] });
        queryClient.invalidateQueries({ queryKey: ['clubRecentActivity', clubId] });
      },
      onError: (error) => {
        console.error('Error logging cash transfer:', error);
        // Handle error message extraction safely
        let errorMessage = 'Failed to log cash transfer';
        if (error instanceof Error) {
          errorMessage = error.message || errorMessage;
        }
        toast.error(errorMessage);
      }
    });
  }

  return (
    <>
      <div className="space-y-6">
        {/* Section 1: Key Metrics Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-3 xl:grid-cols-6 gap-3">
          <MetricCard title="Total Club Value" value={formatCurrency(keyMetrics.totalClubValue)} subtext={`As of ${formatDate(keyMetrics.valuationDate)}`} icon={DollarSign} trend={clubValueTrend} className="xl:col-span-2"/>
          <MetricCard title="Unit Value" value={formatCurrency(keyMetrics.currentUnitValue, true).replace("$+","$").substring(0,8)} subtext="per unit" icon={TrendingUp} />
          <MetricCard title="Total Units" value={formatNumber(keyMetrics.totalUnitsOutstanding)} icon={BookOpen} />
          <MetricCard title="Club Bank & Brokerage Cash" value={formatCurrency(keyMetrics.clubBankBalance + keyMetrics.totalBrokerageCash)} subtext={`Bank: ${formatCurrency(keyMetrics.clubBankBalance)}, Brokerage: ${formatCurrency(keyMetrics.totalBrokerageCash)}`} icon={Banknote} className="xl:col-span-2"/>
          <MetricCard title="Members" value={formatNumber(keyMetrics.membersCount)} icon={Users} />
        </div>

        {/* Section 2: Club Performance Chart */}
        <Card className="bg-white border-slate-200/75 shadow-sm hover:shadow-md transition-all">
          <CardHeader>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center">
              <div>
                  <CardTitle className="text-lg font-medium text-slate-800">Club Performance</CardTitle>
                  <CardDescription className="text-sm text-slate-500">Total club value over time.</CardDescription>
              </div>
              <div className="mt-2 sm:mt-0 flex space-x-1">
                {timeRangeButtons.map(button => (
                  <Button
                    key={button.value}
                    variant={timeRange === button.value ? 'outline' : 'ghost'}
                    size="sm"
                    onClick={() => setTimeRange(button.value)}
                    className={cn(
                      'text-xs px-2.5 py-1 h-auto min-w-[2.5rem]', // Adjusted padding and min-width
                      timeRange === button.value ? 'bg-slate-100 text-blue-600 border-slate-300 font-semibold' : 'text-slate-600 hover:bg-slate-100'
                    )}
                  >
                    {button.label}
                  </Button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-4 h-[350px]">
            {filteredChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={filteredChartData}
                  margin={{ top: 5, right: 20, left: -25, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis
                    dataKey="date"
                    type="number"
                    domain={['dataMin', 'dataMax']}
                    tickFormatter={(tick: number) => formatShortDate(tick)}
                    stroke="#94a3b8"
                    fontSize={12}
                    tickLine={false}
                    axisLine={{ stroke: '#e2e8f0' }}
                  />
                  <YAxis
                    tickFormatter={(tick: number) => `$${Math.round(tick / 1000)}k`}
                    stroke="#94a3b8"
                    fontSize={12}
                    tickLine={false}
                    axisLine={{ stroke: '#e2e8f0' }}
                    domain={['dataMin - 5000', 'auto']} // Adjusted domain for Y-axis
                    allowDataOverflow={false}
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#2563EB', strokeWidth: 1, strokeDasharray: '3 3' }} />
                  <Line
                    type="monotone"
                    dataKey="totalClubValue"
                    name="Total Club Value"
                    stroke="#2563EB"
                    strokeWidth={2.5}
                    dot={filteredChartData.length < 50 ? { r: 3, fill: '#2563EB' } : false} // Show dots for smaller datasets
                    activeDot={{ r: 6, fill: '#2563EB', stroke: '#fff', strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-slate-500">No performance data available for the selected range.</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Rest of the page (Sections 3, 4, 5) as before */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <Card className="bg-white border-slate-200/75 shadow-sm hover:shadow-md transition-all">
              <CardHeader>
                <CardTitle className="text-lg font-medium text-slate-800">Fund Overview</CardTitle>
                <CardDescription className="text-sm text-slate-500">Summary of active investment funds.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {fundSummaries.length > 0 ? fundSummaries.map((fund) => (
                  <Card key={fund.fundId} className="bg-slate-50/50 border-slate-200 shadow-none hover:shadow-sm transition-shadow">
                    <CardHeader className="p-4">
                      <div className="flex justify-between items-start">
                          <Link to={`/club/${clubId}/funds/${fund.fundId}`} className="hover:underline">
                              <CardTitle className="text-md font-medium text-blue-600 hover:text-blue-700">{fund.fundName}</CardTitle>
                          </Link>
                          <span className="text-xs text-slate-500 font-medium tracking-wide whitespace-nowrap">
                              {fund.percentageOfClub !== undefined ? `${formatNumber(fund.percentageOfClub * 100)}% of Club` : 'N/A'}
                          </span>
                      </div>
                      <CardDescription className="text-xs text-slate-500 line-clamp-2 pt-1">{fund.investmentStyle}</CardDescription>
                    </CardHeader>
                    <CardContent className="p-4 pt-0 grid grid-cols-2 gap-x-4 gap-y-1">
                      <div>
                          <p className="text-xs text-slate-500">Fund Value</p>
                          <p className="text-sm font-semibold text-slate-700">{formatCurrency(fund.fundValue)}</p>
                      </div>
                       <div>
                          <p className="text-xs text-slate-500">Brokerage Cash</p>
                          <p className="text-sm font-semibold text-slate-700">{formatCurrency(fund.brokerageCash)}</p>
                      </div>
                    </CardContent>
                  </Card>
                )) : (
                   <p className="text-sm text-slate-500 p-4 text-center">No active funds in this club yet.</p>
                )}
              </CardContent>
            </Card>

            {isAdmin && (
              <Card className="bg-white border-slate-200/75 shadow-sm hover:shadow-md transition-all">
                <CardHeader>
                  <CardTitle className="text-lg font-medium text-slate-800">Quick Actions</CardTitle>
                  <CardDescription className="text-sm text-slate-500">Common administrative tasks.</CardDescription>
                </CardHeader>
                <CardContent className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4 gap-3">
                  <Button
                    variant="outline"
                    className="bg-white w-full justify-start text-left space-x-2 h-auto py-2"
                    onClick={() => setExpenseModalOpen(true)}
                  >
                    <ClipboardPlus className="h-5 w-5 text-blue-600" />
                    <div><span className="block text-sm font-medium text-slate-700">Log Expense</span><span className="block text-xs text-slate-500">Record club spending</span></div>
                  </Button>
                  <Button
                    variant="outline"
                    className="bg-white w-full justify-start text-left space-x-2 h-auto py-2"
                    onClick={() => setMemberTxModalOpen(true)}
                  >
                    <Users className="h-5 w-5 text-blue-600" />
                    <div><span className="block text-sm font-medium text-slate-700">Member D/W</span><span className="block text-xs text-slate-500">Deposits/Withdrawals</span></div>
                  </Button>
                  <Button
                    variant="outline"
                    className="bg-white w-full justify-start text-left space-x-2 h-auto py-2"
                    onClick={() => setCashTransferModalOpen(true)}
                  >
                    <ArrowRightLeft className="h-5 w-5 text-blue-600" />
                    <div><span className="block text-sm font-medium text-slate-700">Bank Transfer</span><span className="block text-xs text-slate-500">To/From Brokerage</span></div>
                  </Button>
                  <Button
                    variant="outline"
                    className="bg-white w-full justify-start text-left space-x-2 h-auto py-2"
                    onClick={handleRecalculate}
                    disabled={isRecalculating}
                  >
                    <RefreshCw className={`h-5 w-5 ${isRecalculating ? 'animate-spin text-slate-400' : 'text-blue-600'}`} />
                    <div>
                      <span className="block text-sm font-medium text-slate-700">
                        {isRecalculating ? 'Recalculating...' : 'Recalculate'}
                      </span>
                      <span className="block text-xs text-slate-500">Run Unit Valuation</span>
                    </div>
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>

          <div className="space-y-6 lg:col-span-1">
            <Card className="bg-white border-slate-200/75 shadow-sm hover:shadow-md transition-all">
              <CardHeader>
                <CardTitle className="text-lg font-medium text-slate-800">Recent Activity</CardTitle>
                <CardDescription className="text-sm text-slate-500">Latest club transactions and events.</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {recentActivity.length > 0 ? (
                  <ul className="divide-y divide-slate-200/75">
                    {recentActivity.slice(0, 5).map((activity) => (
                      <li key={activity.id} className="p-4 hover:bg-slate-50/80 transition-colors">
                        <div className="flex items-start space-x-3">
                          <div className="flex-shrink-0 pt-0.5">
                            {activity.type.includes('Deposit') || activity.type.includes('Dividend') || activity.type.includes('Interest') ?
                              <ArrowUpCircle className="h-5 w-5 text-green-500" /> :
                             activity.type.includes('Withdrawal') || activity.type.includes('Expense') || activity.amount < 0 ?
                              <ArrowDownCircle className="h-5 w-5 text-red-500" /> :
                              <Activity className="h-5 w-5 text-slate-500" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-center">
                              <p className="text-sm font-medium text-slate-700 truncate">
                                {activity.type}
                              </p>
                              <p className="text-xs text-slate-500 whitespace-nowrap">{formatDate(activity.date)}</p>
                            </div>
                            <div className="text-sm text-slate-500 line-clamp-1">
                              <Link to={activity.link || '#'} className="hover:underline">
                                {activity.description}
                              </Link>
                              {activity.fund && <span className="text-xs text-slate-400 ml-1">• {activity.fund}</span>}
                              {activity.member && <span className="text-xs text-slate-400 ml-1">• {activity.member}</span>}
                            </div>
                          </div>
                          <p className={cn(
                            'text-sm font-semibold whitespace-nowrap',
                            activity.amount >= 0 && (
                              activity.type.includes('Deposit') ||
                              activity.type.includes('Dividend') ||
                              activity.type.includes('Interest')
                            ) ? 'text-green-600' : 'text-slate-700'
                          )}>
                            {formatCurrency(activity.amount)}
                          </p>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500 p-4 text-center">No recent activity to display.</p>
                )}
                {recentActivity.length > 5 && (
                  <div className="p-4 border-t border-slate-200/75">
                      <Button variant="outline" size="sm" className="w-full bg-white">View All Activity</Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Modals */}
      {/* Log Expense Modal */}
      <Dialog open={expenseModalOpen} onOpenChange={setExpenseModalOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Log Club Expense</DialogTitle>
          </DialogHeader>
          {clubId && (
            <LogClubExpenseForm
              clubId={clubId || ''}
              onSubmit={async (data) => handleExpenseSubmit(data)}
              onCancel={() => setExpenseModalOpen(false)}
              isSubmitting={isRecordingExpense}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Member Transaction Modal */}
      <Dialog open={memberTxModalOpen} onOpenChange={setMemberTxModalOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Record Member Transaction</DialogTitle>
          </DialogHeader>
          {clubId && (
            <RecordMemberTransactionForm
              clubId={clubId || ''}
              members={clubMembers?.map(member => ({
                id: member.user_id,
                name: `${member.user?.first_name || ''} ${member.user?.last_name || ''}`
              })) || []}
              latestUnitValue={keyMetrics.currentUnitValue}
              latestValuationDate={keyMetrics.valuationDate}
              onSubmit={async (data) => handleMemberTxSubmit(data)}
              onCancel={() => setMemberTxModalOpen(false)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Cash Transfer Modal */}
      <Dialog open={cashTransferModalOpen} onOpenChange={setCashTransferModalOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Log Cash Transfer</DialogTitle>
          </DialogHeader>
          {clubId && (
            <LogCashTransferForm
              clubId={clubId || ''}
              funds={fundSummaries.map(fund => ({ id: fund.fundId, name: fund.fundName })) || []}
              onSubmit={async (data) => handleCashTransferSubmit(data)}
              onCancel={() => setCashTransferModalOpen(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ClubDashboardPage;
