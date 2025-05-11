
// frontend/src/pages/ClubDashboardPage.tsx
import React, { useState, useMemo } from 'react'; // Added useMemo
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
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

// Mock data - replace with API calls
const MOCK_PERFORMANCE_DATA_ALL_TIME = [
  { date: '2023-01-15', totalClubValue: 95000 },
  { date: '2023-02-15', totalClubValue: 98000 },
  { date: '2023-03-15', totalClubValue: 97000 },
  { date: '2023-04-15', totalClubValue: 102000 },
  { date: '2023-05-15', totalClubValue: 105000 },
  { date: '2023-06-15', totalClubValue: 108000 }, 
  { date: '2023-07-15', totalClubValue: 110000 },
  { date: '2023-08-15', totalClubValue: 112000 },
  { date: '2023-09-15', totalClubValue: 115000 },
  { date: '2023-10-15', totalClubValue: 113000 },
  { date: '2023-11-15', totalClubValue: 118000 },
  { date: '2023-12-15', totalClubValue: 120000 },
  { date: '2024-01-01', totalClubValue: 100000 }, // Deliberate reset for YTD example
  { date: '2024-01-15', totalClubValue: 122000 }, 
  { date: '2024-02-01', totalClubValue: 105000 },
  { date: '2024-02-15', totalClubValue: 123000 },
  { date: '2024-03-01', totalClubValue: 102000 },
  { date: '2024-03-15', totalClubValue: 125000 },
  { date: '2024-04-01', totalClubValue: 110000 },
  { date: '2024-04-15', totalClubValue: 128000 },
  { date: '2024-05-01', totalClubValue: 115000 },
  { date: '2024-05-15', totalClubValue: 130000 },
  { date: '2024-06-01', totalClubValue: 120000 },
  { date: '2024-06-15', totalClubValue: 132000 },
  { date: '2024-07-01', totalClubValue: 122000 },
  { date: '2024-07-15', totalClubValue: 135000 },
  { date: '2024-07-28', totalClubValue: 125034.78 }, // Current date in mock
];

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
  fundValue: number;
  brokerageCash: number;
  percentageOfClub: number;
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

export interface ClubDashboardResponse {
  isLoading: boolean;
  error: string | null;
  data: ClubDashboardData;
}

const MOCK_CLUB_DASHBOARD_DATA: ClubDashboardResponse = {
  isLoading: false,
  error: null,
  data: {
    clubId: 'club123',
    clubName: 'Eagle Investors Club',
    keyMetrics: {
      totalClubValue: 125034.78,
      valuationDate: '2024-07-28',
      previousClubValue: 124500.00,
      currentUnitValue: 12.5035,
      totalUnitsOutstanding: 10000,
      clubBankBalance: 25034.78,
      totalBrokerageCash: 15000.00,
      membersCount: 12,
    },
    performanceChartData: MOCK_PERFORMANCE_DATA_ALL_TIME,
    isAdmin: true,
    fundSummaries: [
      {
        fundId: 'fundA',
        fundName: 'US Equities Fund',
        fundValue: 75000,
        brokerageCash: 5000,
        percentageOfClub: 0.60,
        investmentStyle: 'Focus on S&P 500 Index ETFs and large-cap stocks.'
      },
      {
        fundId: 'fundB',
        fundName: 'Global Growth Fund',
        fundValue: 35000,
        brokerageCash: 10000,
        percentageOfClub: 0.28,
        investmentStyle: 'Diversified international equities with high growth potential.'
      },
    ],
    recentActivity: [
      { id: 'act1', date: '2024-07-27', type: 'Deposit', member: 'John D.', description: 'Member Deposit', amount: 500, link: '/club/club123/members/mem123' },
      { id: 'act2', date: '2024-07-26', type: 'Club Expense', description: 'Accounting Software Subscription', amount: -50, link: '/club/club123/accounting' },
      { id: 'act3', date: '2024-07-25', type: 'Buy Stock', fund: 'US Equities Fund', description: 'Bought 10 shares of MSFT', amount: -3450, link: '/club/club123/brokerage-log/tx12345' },
      { id: 'act4', date: '2024-07-24', type: 'Bank to Brokerage', description: 'Transfer to US Equities Fund', amount: -10000, link: '/club/club123/accounting' },
    ],
  },
};

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
  const { data: dashboardData, isLoading, error } = MOCK_CLUB_DASHBOARD_DATA;
  const [timeRange, setTimeRange] = useState('YTD');
  
  // Modal states for forms
  const [expenseModalOpen, setExpenseModalOpen] = useState(false);
  const [memberTxModalOpen, setMemberTxModalOpen] = useState(false);
  const [cashTransferModalOpen, setCashTransferModalOpen] = useState(false);
  const [isRecalculating, setIsRecalculating] = useState(false);

  const allChartData = useMemo(() => {
    return dashboardData?.performanceChartData.map((d) => ({
      ...d,
      date: new Date(d.date).getTime(), // Convert to timestamp for easier filtering
    })).sort((a, b) => a.date - b.date) || []; // Ensure data is sorted by date
  }, [dashboardData?.performanceChartData]);

  const filteredChartData = useMemo(() => {
    if (!allChartData.length) return [];
    const now = new Date(dashboardData?.keyMetrics.valuationDate || Date.now()); // Use valuationDate as 'today' for consistency
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

  }, [allChartData, timeRange, dashboardData?.keyMetrics.valuationDate]);

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

  // Error state
  if (error || !dashboardData) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-red-50 border border-red-200 rounded-lg">
        <div className="text-red-500 mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-red-700 mb-2">Unable to Load Dashboard Data</h3>
        <p className="text-red-600 text-center mb-4">
          {error || "There was a problem retrieving the club dashboard data. Please try again later."}
        </p>
        <Button variant="outline" className="bg-white border-red-300 text-red-700 hover:bg-red-50">
          Retry
        </Button>
      </div>
    );
  }

  // Ensure dashboardData is available before destructuring
  if (!dashboardData) {
    return null;
  }

  const { keyMetrics, isAdmin, fundSummaries, recentActivity } = dashboardData;
  const clubValueTrend = keyMetrics.totalClubValue > keyMetrics.previousClubValue ? 'up' : (keyMetrics.totalClubValue < keyMetrics.previousClubValue ? 'down' : 'neutral');

  const timeRangeButtons = [
    { label: '1M', value: '1M' }, { label: '3M', value: '3M' }, { label: '6M', value: '6M' },
    { label: 'YTD', value: 'YTD' }, { label: '1Y', value: '1Y' }, { label: 'All', value: 'All' },
  ];

  // Handler for recalculate button
  async function handleRecalculate() {
    if (!clubId) return;
    
    setIsRecalculating(true);
    toast.info('Starting club valuation recalculation...');
    
    try {
      // In a real implementation, this would be an actual API call
      // const apiClient = createApiClient(getAccessTokenSilently);
      // await apiClient(`/api/v1/clubs/${clubId}/recalculate`, { method: 'POST' });
      
      // Simulate API call for mock data
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      toast.success('Club valuation recalculated successfully');
      
      // In a real implementation, refresh dashboard data
      // const response = await apiClient(`/api/v1/clubs/${clubId}/dashboard`);
      // const data = await response.json();
      // setDashboardData(data);
    } catch (error) {
      console.error('Error recalculating club valuation:', error);
      toast.error('Failed to recalculate club valuation');
    } finally {
      setIsRecalculating(false);
    }
  }

  // Handler for expense form submission
  async function handleExpenseSubmit(formData: ClubExpenseFormData) {
    try {
      // In a real implementation, this would be an actual API call
      // Example:
      // const response = await fetch('/api/v1/transactions/club-expense', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(formData)
      // });
      
      console.log('Submitting expense:', formData);
      
      // Simulate API call for mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast.success('Club expense logged successfully');
      setExpenseModalOpen(false);
      
      // In a real implementation, refresh dashboard data
      // const dashboardResponse = await fetch(`/api/v1/clubs/${clubId}/dashboard`);
      // const dashboardData = await dashboardResponse.json();
      // setDashboardData(dashboardData);
    } catch (error) {
      console.error('Error logging club expense:', error);
      throw error;
    }
  }

  // Handler for member transaction form submission
  async function handleMemberTxSubmit(formData: MemberTransactionFormData) {
    try {
      // In a real implementation, this would be an actual API call
      // Example:
      // const response = await fetch('/api/v1/transactions/member', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(formData)
      // });
      
      console.log('Submitting member transaction:', formData);
      
      // Simulate API call for mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast.success('Member transaction recorded successfully');
      setMemberTxModalOpen(false);
      
      // In a real implementation, refresh dashboard data
      // const dashboardResponse = await fetch(`/api/v1/clubs/${clubId}/dashboard`);
      // const dashboardData = await dashboardResponse.json();
      // setDashboardData(dashboardData);
    } catch (error) {
      console.error('Error recording member transaction:', error);
      throw error;
    }
  }

  // Handler for cash transfer form submission
  async function handleCashTransferSubmit(formData: CashTransferFormData) {
    try {
      // In a real implementation, this would be an actual API call
      // Example:
      // const response = await fetch('/api/v1/transactions/cash-transfer', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(formData)
      // });
      
      console.log('Submitting cash transfer:', formData);
      
      // Simulate API call for mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast.success('Cash transfer logged successfully');
      setCashTransferModalOpen(false);
      
      // In a real implementation, refresh dashboard data
      // const dashboardResponse = await fetch(`/api/v1/clubs/${clubId}/dashboard`);
      // const dashboardData = await dashboardResponse.json();
      // setDashboardData(dashboardData);
    } catch (error) {
      console.error('Error logging cash transfer:', error);
      throw error;
    }
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
                              {formatNumber(fund.percentageOfClub * 100)}% of Club
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
                            {activity.type === 'Deposit' ? <ArrowUpCircle className="h-5 w-5 text-green-500" /> :
                             activity.type === 'Withdrawal' || activity.amount < 0 ? <ArrowDownCircle className="h-5 w-5 text-red-500" /> :
                             <Activity className="h-5 w-5 text-slate-500" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between items-center">
                              <p className="text-sm font-medium text-slate-700 truncate">
                                {activity.type.startsWith('Buy') || activity.type.startsWith('Sell') ? `${activity.type} (${activity.fund || 'N/A'})` : activity.type}
                              </p>
                              <p className="text-xs text-slate-500 whitespace-nowrap">{formatDate(activity.date)}</p>
                            </div>
                            <Link to={activity.link || '#'} className="text-sm text-slate-500 hover:underline line-clamp-1">
                              {activity.description}
                              {activity.member && <span className="italic"> by {activity.member}</span>}
                            </Link>
                          </div>
                          <p className={cn(
                            'text-sm font-semibold whitespace-nowrap',
                            activity.amount >= 0 && (activity.type === 'Deposit' || activity.type === 'Interest') ? 'text-green-600' : 'text-slate-700'
                          )}>
                            {formatCurrency(activity.amount, activity.type === 'Deposit' || activity.type === 'Interest')}
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
              onSubmit={handleExpenseSubmit}
              onCancel={() => setExpenseModalOpen(false)}
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
              members={[
                { id: 'user1', name: 'John Doe' },
                { id: 'user2', name: 'Jane Smith' },
                { id: 'user3', name: 'Robert Johnson' }
              ]} // Mock data for members
              latestUnitValue={dashboardData?.keyMetrics.currentUnitValue}
              latestValuationDate={dashboardData?.keyMetrics.valuationDate}
              onSubmit={handleMemberTxSubmit}
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
              funds={dashboardData?.fundSummaries.map(fund => ({ id: fund.fundId, name: fund.fundName })) || []}
              onSubmit={handleCashTransferSubmit}
              onCancel={() => setCashTransferModalOpen(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ClubDashboardPage;
