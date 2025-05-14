// frontend/src/pages/FundDetailPage.tsx
import { useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowLeft, Banknote, DollarSign, TrendingUp, ListChecks, Percent, Edit, PlusCircle, Info, Loader2, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip } from 'recharts'; // Renamed Tooltip to avoid conflict if any
import { useAuth0 } from '@auth0/auth0-react';

// Import API hooks
import {
  useClubFunds,
  useClubMembers,
  useFundSplits,
  useAssets,
  useFundDetails,
  useFundPerformanceHistory,
  useFundTransactions,
  useClubPortfolio
} from '@/hooks/useApi';

// No need to import types that we're not using directly

// Define a custom type for the fund with brokerage_cash_balance
interface ExtendedFund {
  id: string;
  club_id: string;
  name: string;
  description?: string;
  is_active: boolean;
  brokerage_cash_balance: number;
  created_at: string;
  updated_at: string;
}

// --- Helper Functions ---
const formatCurrency = (value?: number | null, withSign = false) => {
  if (value == null) return 'N/A';
  const options: Intl.NumberFormatOptions = { style: 'currency', currency: 'USD' };
  if (withSign) options.signDisplay = 'exceptZero';
  return new Intl.NumberFormat('en-US', options).format(value);
};

const formatNumber = (value?: number | null, precision = 2) => {
  if (value == null) return 'N/A';
  return new Intl.NumberFormat('en-US', { minimumFractionDigits: precision, maximumFractionDigits: precision }).format(value);
};

const formatDate = (dateInput?: string | number | Date) => {
  if (!dateInput) return 'N/A';
  return new Date(dateInput).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

// Function removed as it's not used in this implementation

// Recharts Custom Tooltip for Fund Performance
interface FundPerformanceTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    // Potentially other properties from Recharts payload if needed
  }>;
  label?: string | number;
}

const FundPerformanceTooltip = ({ active, payload, label }: FundPerformanceTooltipProps) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 shadow-lg rounded-lg border border-slate-200">
        <p className="text-xs text-slate-500">{formatDate(label)}</p>
        <p className="text-sm font-medium text-slate-800">
          Fund Value: <span className="text-blue-600 font-bold">{formatCurrency(payload[0].value)}</span>
        </p>
      </div>
    );
  }
  return null;
};

// --- Main Component ---
const FundDetailPage = () => {
  const { clubId = "", fundId = "" } = useParams<{ clubId: string; fundId: string }>();
  const { user } = useAuth0();

  // Fetch data using React Query hooks
  const { data: funds = [], isLoading: isLoadingFunds } = useClubFunds(clubId);
  const { isLoading: isLoadingAssets } = useAssets();
  const { data: members = [], isLoading: isLoadingMembers } = useClubMembers(clubId);
  const { data: fundSplits = [], isLoading: isLoadingFundSplits } = useFundSplits(clubId);
  const { data: fundDetails, isLoading: isLoadingFundDetails } = useFundDetails(clubId, fundId);
  const { data: performanceHistory, isLoading: isLoadingPerformanceHistory } = useFundPerformanceHistory(clubId, fundId);
  const { data: portfolio, isLoading: isLoadingPortfolioData } = useClubPortfolio(clubId);
  const { data: transactionData = [], isLoading: isLoadingTransactionsData } = useFundTransactions(clubId, fundId);
  
  // Find the current fund from the funds list
  const fund = funds.find(f => f.id === fundId);
  const fundError = !fund && !isLoadingFunds ? new Error("Fund not found") : null;
  
  // Extract positions from portfolio data
  const positions = useMemo(() => {
    if (!portfolio || !portfolio.positions) return [];
    // In a real implementation, we would filter positions by fund_id
    // For now, we'll return all positions as we don't have fund filtering in the API yet
    return portfolio.positions;
  }, [portfolio]);

  // Determine if user is admin
  const isAdmin = members?.some(member =>
    member.user_id === user?.sub && member.role === 'ADMIN'
  ) || false;

  // Calculate fund metrics
  const fundMetrics = useMemo(() => {
    if (!fund) return null;

    // Use fundDetails if available, otherwise calculate from positions
    if (fundDetails) {
      // Get the fund split percentage for this fund
      const fundSplit = fundSplits.find(split => split.fund_id === fundId);
      const fundSplitPercentage = fundSplit ? fundSplit.percentage : 0;

      return {
        totalFundValue: fundDetails.total_value,
        assetsMarketValue: fundDetails.positions_market_value,
        cashBalance: fundDetails.cash_balance,
        percentOfClub: fundDetails.percentage_of_club_assets,
        numberOfPositions: positions.length,
        fundSplitPercentage,
        // These values might not be directly available in fundDetails
        assetsCostBasis: positions.reduce((sum, pos) => sum + pos.cost_basis, 0),
        unrealizedPandL: positions.reduce((sum, pos) => sum + pos.unrealized_gain_loss, 0)
      };
    } else {
      // Calculate from positions as fallback
      const assetsMarketValue = positions.reduce((sum, pos) => sum + pos.market_value, 0);
      const assetsCostBasis = positions.reduce((sum, pos) => sum + pos.cost_basis, 0);
      const unrealizedPandL = positions.reduce((sum, pos) => sum + pos.unrealized_gain_loss, 0);
      
      // Get the fund split percentage for this fund
      const fundSplit = fundSplits.find(split => split.fund_id === fundId);
      const fundSplitPercentage = fundSplit ? fundSplit.percentage : 0;
      
      // Use fund's cash balance if available, otherwise default to 0
      // Type assertion to access brokerage_cash_balance
      const cashBalance = (fund as ExtendedFund).brokerage_cash_balance || 0;
      
      // Calculate total fund value
      const totalFundValue = assetsMarketValue + cashBalance;

      return {
        totalFundValue,
        assetsMarketValue,
        assetsCostBasis,
        unrealizedPandL,
        percentOfClub: 0, // We don't have this without fundDetails
        numberOfPositions: positions.length,
        fundSplitPercentage,
        cashBalance
      };
    }
  }, [fund, fundDetails, positions, fundSplits, fundId]);

  // Generate chart data from performance history
  const chartData = useMemo(() => {
    if (!fundMetrics) return [];

    // Use performance history data if available
    if (performanceHistory && performanceHistory.history && performanceHistory.history.length > 0) {
      return performanceHistory.history.map(point => ({
        date: new Date(point.valuation_date).getTime(),
        value: point.total_value
      }));
    }

    // Fallback to placeholder data if no performance history
    const today = new Date();
    const oneMonthAgo = new Date(today);
    oneMonthAgo.setMonth(today.getMonth() - 1);
    
    const twoMonthsAgo = new Date(today);
    twoMonthsAgo.setMonth(today.getMonth() - 2);
    
    const threeMonthsAgo = new Date(today);
    threeMonthsAgo.setMonth(today.getMonth() - 3);

    return [
      { date: threeMonthsAgo.getTime(), value: fundMetrics.totalFundValue * 0.9 },
      { date: twoMonthsAgo.getTime(), value: fundMetrics.totalFundValue * 0.95 },
      { date: oneMonthAgo.getTime(), value: fundMetrics.totalFundValue * 0.98 },
      { date: today.getTime(), value: fundMetrics.totalFundValue }
    ];
  }, [fundMetrics, performanceHistory]);

  // Loading state
  const isLoading = isLoadingFunds || isLoadingFundDetails || isLoadingPerformanceHistory ||
                   isLoadingAssets || isLoadingMembers || isLoadingFundSplits ||
                   isLoadingPortfolioData || isLoadingTransactionsData;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading fund details...</p>
        </div>
      </div>
    );
  }

  if (fundError || !fund || !fundMetrics) {
    return (
      <div className="space-y-6">
        <Button variant="outline" asChild className="mb-4 bg-white">
          <Link to={`/club/${clubId}/funds`}><ArrowLeft className="mr-2 h-4 w-4" /> Back to Funds</Link>
        </Button>
        <Card className="bg-red-50 border-red-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-6 w-6 text-red-600" />
              <CardTitle className="text-red-700">Error Loading Fund Details</CardTitle>
            </div>
          </CardHeader>
          <CardContent><p className="text-red-600">Could not load details for this fund. It might not exist or an error occurred.</p></CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Back Button & Page Title */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <div>
            <Button variant="outline" asChild className="mb-2 bg-white text-slate-600 hover:text-slate-800 border-slate-300 hover:bg-slate-50">
              <Link to={`/club/${clubId}/funds`}><ArrowLeft className="mr-2 h-4 w-4" /> Back to Funds</Link>
            </Button>
            <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">{fund.name}</h1>
        </div>
        {isAdmin && (
             <Button className="bg-blue-600 hover:bg-blue-700">
                <PlusCircle className="mr-2 h-4 w-4" /> Log Trade for this Fund
            </Button>
        )}
      </div>

      {/* Fund Description */}
      {fund.description && (
        <Card className="bg-white border-slate-200/75 shadow-sm">
            <CardHeader><CardTitle className="text-lg font-medium text-slate-800 flex items-center"><Info className="mr-2 h-5 w-5 text-blue-600"/>Fund Overview</CardTitle></CardHeader>
            <CardContent><p className="text-sm text-slate-700 leading-relaxed">{fund.description}</p></CardContent>
        </Card>
      )}

      {/* Section 1: Key Fund Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {[ 
          { title: 'Total Fund Value', value: formatCurrency(fundMetrics.totalFundValue), icon: DollarSign },
          { title: 'Brokerage Cash', value: formatCurrency(fundMetrics.cashBalance), icon: Banknote },
          { title: '# of Positions', value: formatNumber(fundMetrics.numberOfPositions, 0), icon: ListChecks },
          { title: '% of Club Assets', value: `${formatNumber(fundMetrics.percentOfClub, 1)}%`, icon: Percent },
          { title: 'New Cash Allocation', value: `${formatNumber(fundMetrics.fundSplitPercentage * 100, 0)}%`, icon: TrendingUp },
        ].map(metric => (
          <Card key={metric.title} className="bg-white border-slate-200/75 shadow-sm">
            <CardHeader className="pb-1.5"><CardTitle className="text-[0.7rem] font-medium text-slate-500 uppercase tracking-wider flex justify-between items-center">{metric.title} <metric.icon className="h-4 w-4 text-slate-400" /></CardTitle></CardHeader>
            <CardContent><div className="text-xl font-bold text-slate-900">{metric.value}</div></CardContent>
          </Card>
        ))}
      </div>
      
      {/* Section 2: Fund Performance Chart */}
      <Card className="bg-white border-slate-200/75 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-medium text-slate-800">Fund Performance</CardTitle>
          <CardDescription className="text-sm text-slate-500">Fund value over time.</CardDescription>
        </CardHeader>
        <CardContent className="p-4 h-[300px]">
        {chartData.length > 1 ? (
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 20, left: -25, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false}/>
                    <XAxis dataKey="date" type="number" domain={['dataMin', 'dataMax']} tickFormatter={(tick) => formatDate(new Date(tick).toISOString())} stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={{stroke: '#e2e8f0'}}/>
                    <YAxis tickFormatter={(tick) => `$${Math.round(tick/1000)}k`} stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={{stroke: '#e2e8f0'}} domain={['dataMin - 2000', 'auto']}/>
                    <RechartsTooltip content={<FundPerformanceTooltip />} cursor={{stroke: '#2563EB', strokeWidth: 1, strokeDasharray: '3 3'}}/>
                    <Line type="monotone" dataKey="value" name="Fund Value" stroke="#2563EB" strokeWidth={2} dot={chartData.length < 30} activeDot={{r:6, fill: '#2563EB', stroke: '#fff', strokeWidth:2}}/>
                </LineChart>
            </ResponsiveContainer>
             ) : (
            <div className="flex items-center justify-center h-full text-slate-500">Not enough data for performance chart.</div>
          )}
        </CardContent>
      </Card>

      {/* Section 3: Holdings Table */}
      <Card className="bg-white border-slate-200/75 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-medium text-slate-800">Holdings ({fundMetrics.numberOfPositions})</CardTitle>
          <CardDescription className="text-sm text-slate-500">Current investment positions in this fund.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {positions.length > 0 ? (
            <Table>
              <TableHeader><TableRow className="hover:bg-transparent"><TableHead>Asset</TableHead><TableHead className="text-right">Qty</TableHead><TableHead className="text-right">Avg. Cost</TableHead><TableHead className="text-right">Current Price</TableHead><TableHead className="text-right">Market Value</TableHead><TableHead className="text-right">Unreal. P&L</TableHead><TableHead className="text-right">% of Fund</TableHead>{isAdmin && <TableHead className="w-[80px]"></TableHead>}</TableRow></TableHeader>
              <TableBody>
                {positions.map((pos, index) => {
                  const percentOfFund = fundMetrics.totalFundValue > 0 ? (pos.market_value / fundMetrics.totalFundValue) * 100 : 0;
                  
                  return (
                    <TableRow key={`${pos.asset_id}-${index}`} className="hover:bg-slate-50/50">
                      <TableCell>
                        <div className="font-medium text-slate-800">{pos.asset_symbol}</div>
                        <div className="text-xs text-slate-500 truncate max-w-[150px]">{pos.asset_name}</div>
                      </TableCell>
                      <TableCell className="text-right font-medium text-slate-700">{formatNumber(pos.quantity, 2)}</TableCell>
                      <TableCell className="text-right text-slate-600">{formatCurrency(pos.cost_basis / pos.quantity)}</TableCell>
                      <TableCell className="text-right text-slate-600">{formatCurrency(pos.current_price)}</TableCell>
                      <TableCell className="text-right font-semibold text-slate-800">{formatCurrency(pos.market_value)}</TableCell>
                      <TableCell className={cn("text-right font-medium", pos.unrealized_gain_loss >=0 ? 'text-green-600' : 'text-red-600')}>
                        {formatCurrency(pos.unrealized_gain_loss, true)}
                      </TableCell>
                      <TableCell className="text-right text-slate-600">{formatNumber(percentOfFund, 1)}%</TableCell>
                      {isAdmin && <TableCell className="text-center"><Button variant="ghost" size="icon" className="h-7 w-7 text-slate-500 hover:text-blue-600"><Edit className="h-4 w-4"/><span className="sr-only">Edit</span></Button></TableCell>}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-slate-500 text-center py-6">No holdings in this fund yet.</p>
          )}
        </CardContent>
      </Card>

      {/* Section 4: Recent Fund Transactions */}
      <Card className="bg-white border-slate-200/75 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-medium text-slate-800">Recent Transactions</CardTitle>
          <CardDescription className="text-sm text-slate-500">Last 10 transactions for {fund.name}.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {transactionData.length > 0 ? (
            <Table>
              <TableHeader><TableRow className="hover:bg-transparent"><TableHead>Date</TableHead><TableHead>Type</TableHead><TableHead>Asset</TableHead><TableHead className="text-right">Qty</TableHead><TableHead className="text-right">Price/Unit</TableHead><TableHead className="text-right">Total</TableHead><TableHead>Notes</TableHead></TableRow></TableHeader>
              <TableBody>
                {transactionData.slice(0, 10).map(tx => {
                  return (
                    <TableRow key={tx.id} className="hover:bg-slate-50/50">
                      <TableCell className="text-xs text-slate-600">{formatDate(tx.transaction_date)}</TableCell>
                      <TableCell className="text-sm font-medium text-slate-700">{tx.transaction_type}</TableCell>
                      <TableCell className="text-sm text-slate-600">{tx.asset?.symbol || 'N/A'}</TableCell>
                      <TableCell className="text-right text-sm text-slate-600">{tx.quantity !== undefined ? formatNumber(tx.quantity, 2) : 'N/A'}</TableCell>
                      <TableCell className="text-right text-sm text-slate-600">{tx.price_per_unit !== undefined ? formatCurrency(tx.price_per_unit) : 'N/A'}</TableCell>
                      <TableCell className={cn("text-right text-sm font-semibold", tx.amount >=0 ? "text-green-600" : "text-red-600")}>{formatCurrency(tx.amount)}</TableCell>
                      <TableCell className="text-xs text-slate-500 truncate max-w-[200px]">{tx.notes || '-'}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-slate-500 text-center py-6">No transactions recorded for this fund yet.</p>
          )}
          {transactionData.length > 10 && (
            <CardFooter className="pt-4 border-t border-slate-200/75">
                <Button variant="outline" size="sm" asChild className="w-full sm:w-auto bg-white">
                    <Link to={`/club/${clubId}/brokerage-log?fundId=${fundId}`}>View All Transactions for this Fund</Link>
                </Button>
            </CardFooter>
          )}
        </CardContent>
      </Card>

    </div>
  );
};

export default FundDetailPage;
