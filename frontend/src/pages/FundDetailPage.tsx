
// frontend/src/pages/FundDetailPage.tsx
import React, { useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, DollarSign, TrendingUp, TrendingDown, ListChecks, Hash, Percent, Edit, PlusCircle, BookOpen, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip } from 'recharts'; // Renamed Tooltip to avoid conflict if any

// --- Mock Data Structures ---
interface Asset {
  id: string;
  symbol: string;
  name: string;
  current_price: number; // Manual entry for MVP
  asset_type?: 'STOCK' | 'OPTION' | 'CRYPTO';
}

interface Position {
  id: string;
  asset_id: string;
  quantity: number;
  average_cost_basis: number;
}

interface Transaction {
  id: string;
  transaction_date: string;
  transaction_type: string; // e.g., BuyStock, SellOption, Dividend
  asset_id?: string; // Optional, as some transactions might not be asset-specific (e.g., Fee)
  quantity?: number;
  price_per_unit?: number;
  total_amount: number;
  description?: string;
  fees_commissions?: number;
}

interface FundDetails {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  brokerage_cash_balance: number;
  positions: Position[];
  transactions: Transaction[]; // Transactions specific to this fund
  // fund_split_percentage: number; // From club.fund_splits for this fund_id
}

// Assume club total value is passed or fetched separately for % of Club Assets calculation
interface FundDetailPageData {
  fund: FundDetails;
  assets: Asset[]; // All assets, to resolve asset details for positions/transactions
  clubTotalValue: number; // For calculating % of total club assets
  fundSplitPercentage: number; // New cash allocation for this fund
  isAdmin: boolean;
  // For Fund Performance Chart (simplified example)
  performanceData?: { date: string; value: number }[]; 
}

// --- Mock Data Generation ---
const MOCK_ASSETS_STORE_FD: Asset[] = [
  { id: 'asset1', symbol: 'AAPL', name: 'Apple Inc.', current_price: 175.50, asset_type: 'STOCK' },
  { id: 'asset2', symbol: 'MSFT', name: 'Microsoft Corp.', current_price: 340.20, asset_type: 'STOCK' },
  { id: 'assetOption1', symbol: 'AAPL251219C180', name: 'AAPL $180 CALL Exp 2025-12-19', current_price: 10.50, asset_type: 'OPTION' },
];

const MOCK_FUND_DETAIL_PAGE_DATA: (fundId?: string) => FundDetailPageData | null = (fundId = 'fundA') => {
  if (fundId !== 'fundA') return null; // Only mocking one fund for now
  return {
    fund: {
      id: 'fundA',
      name: 'US Equities Fund',
      description: 'Focuses on S&P 500 Index ETFs and large-cap stocks with a long-term growth perspective. Aims to outperform the benchmark through strategic sector allocation and individual stock picking.',
      is_active: true,
      brokerage_cash_balance: 5000.25,
      positions: [
        { id: 'pos1', asset_id: 'asset1', quantity: 50, average_cost_basis: 150.00 },
        { id: 'pos2', asset_id: 'asset2', quantity: 25, average_cost_basis: 300.00 },
        // { id: 'posOpt1', asset_id: 'assetOption1', quantity: 10, average_cost_basis: 8.00 },
      ],
      transactions: [
        { id: 'tx1', transaction_date: '2024-07-20', transaction_type: 'BuyStock', asset_id: 'asset1', quantity: 10, price_per_unit: 170.00, total_amount: -1700.00, description: 'Purchased Apple shares' },
        { id: 'tx2', transaction_date: '2024-07-15', transaction_type: 'Dividend', asset_id: 'asset2', total_amount: 25.00, description: 'MSFT Dividend Payout' },
        { id: 'tx3', transaction_date: '2024-07-01', transaction_type: 'SellStock', asset_id: 'asset1', quantity: 5, price_per_unit: 175.00, total_amount: 875.00, fees_commissions: 1.00, description: 'Sold some Apple shares' },
        // { id: 'txOptBuy', transaction_date: '2024-06-10', transaction_type: 'BuyOption', asset_id: 'assetOption1', quantity: 10, price_per_unit: 8.00, total_amount: -800.00, description: 'BTO AAPL Calls' },
      ],
    },
    assets: MOCK_ASSETS_STORE_FD,
    clubTotalValue: 125034.78, // From Club Dashboard for example
    fundSplitPercentage: 0.6, // 60%
    isAdmin: true,
    performanceData: [
        { date: '2024-04-01', value: 68000 },
        { date: '2024-05-01', value: 70000 },
        { date: '2024-06-01', value: 72000 },
        { date: '2024-07-01', value: 75000 },
        { date: '2024-07-28', value: (50 * 175.50) + (25 * 340.20) + 5000.25 }, // Calculated current fund value
    ]
  };
};

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

const formatDate = (dateString?: string) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

const getAssetById = (assetId: string, assets: Asset[]) => assets.find(a => a.id === assetId);

// --- Fund Metrics Calculation ---
const calculateFundDetailedMetrics = (fund: FundDetails, assets: Asset[], clubTotalValue: number) => {
  let assetsMarketValue = 0;
  let assetsCostBasis = 0;
  fund.positions.forEach(pos => {
    const asset = getAssetById(pos.asset_id, assets);
    if (asset) {
      assetsMarketValue += pos.quantity * asset.current_price;
      assetsCostBasis += pos.quantity * pos.average_cost_basis;
    }
  });
  const totalFundValue = assetsMarketValue + fund.brokerage_cash_balance;
  const unrealizedPandL = assetsMarketValue - assetsCostBasis;
  const percentOfClub = clubTotalValue > 0 ? (totalFundValue / clubTotalValue) * 100 : 0;
  return { totalFundValue, assetsMarketValue, assetsCostBasis, unrealizedPandL, percentOfClub, numberOfPositions: fund.positions.length };
};

// Recharts Custom Tooltip for Fund Performance
const FundPerformanceTooltip = ({ active, payload, label }: any) => {
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
  const { clubId, fundId } = useParams<{ clubId: string; fundId: string }>();
  // const { data, isLoading, error } = useQuery(...); // Real API call
  const [pageData, setPageData] = useState<FundDetailPageData | null>(MOCK_FUND_DETAIL_PAGE_DATA(fundId));
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fundMetrics = useMemo(() => {
    if (!pageData?.fund) return null;
    return calculateFundDetailedMetrics(pageData.fund, pageData.assets, pageData.clubTotalValue);
  }, [pageData]);

  const chartData = useMemo(() => {
    return pageData?.performanceData?.map(d => ({...d, date: new Date(d.date).getTime()})).sort((a,b) => a.date - b.date) || [];
  }, [pageData?.performanceData]);


  if (isLoading) { /* ... Skeleton ... */ }
  if (error || !pageData || !fundMetrics) {
    return (
      <div className="space-y-6">
        <Button variant="outline" asChild className="mb-4 bg-white">
          <Link to={`/club/${clubId}/funds`}><ArrowLeft className="mr-2 h-4 w-4" /> Back to Funds</Link>
        </Button>
        <Card className="bg-red-50 border-red-200">
          <CardHeader><CardTitle className="text-red-700">Error Loading Fund Details</CardTitle></CardHeader>
          <CardContent><p className="text-red-600">Could not load details for this fund. It might not exist or an error occurred.</p></CardContent>
        </Card>
      </div>
    );
  }

  const { fund, assets, fundSplitPercentage, isAdmin } = pageData;

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
          { title: 'Brokerage Cash', value: formatCurrency(fund.brokerage_cash_balance), icon: Banknote },
          { title: '# of Positions', value: formatNumber(fundMetrics.numberOfPositions, 0), icon: ListChecks },
          { title: '% of Club Assets', value: `${formatNumber(fundMetrics.percentOfClub, 1)}%`, icon: Percent },
          { title: 'New Cash Allocation', value: `${formatNumber(fundSplitPercentage * 100, 0)}%`, icon: TrendingUp },
        ].map(metric => (
          <Card key={metric.title} className="bg-white border-slate-200/75 shadow-sm">
            <CardHeader className="pb-1.5"><CardTitle className="text-[0.7rem] font-medium text-slate-500 uppercase tracking-wider flex justify-between items-center">{metric.title} <metric.icon className="h-4 w-4 text-slate-400" /></CardTitle></CardHeader>
            <CardContent><div className="text-xl font-bold text-slate-900">{metric.value}</div></CardContent>
          </Card>
        ))}
      </div>
      
      {/* Section 2: Fund Performance Chart - Placeholder for now */}
      <Card className="bg-white border-slate-200/75 shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-medium text-slate-800">Fund Performance</CardTitle>
          <CardDescription className="text-sm text-slate-500">Fund value over time. (Simplified chart)</CardDescription>
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
          {fund.positions.length > 0 ? (
            <Table>
              <TableHeader><TableRow className="hover:bg-transparent"><TableHead>Asset</TableHead><TableHead className="text-right">Qty</TableHead><TableHead className="text-right">Avg. Cost</TableHead><TableHead className="text-right">Current Price</TableHead><TableHead className="text-right">Market Value</TableHead><TableHead className="text-right">Unreal. P&L</TableHead><TableHead className="text-right">% of Fund</TableHead>{isAdmin && <TableHead className="w-[80px]"></TableHead>}</TableRow></TableHeader>
              <TableBody>
                {fund.positions.map(pos => {
                  const asset = getAssetById(pos.asset_id, assets);
                  if (!asset) return <TableRow key={pos.id}><TableCell colSpan={isAdmin ? 8:7}>Asset details not found.</TableCell></TableRow>;
                  const marketValue = pos.quantity * asset.current_price;
                  const costBasis = pos.quantity * pos.average_cost_basis;
                  const unrealizedPandL = marketValue - costBasis;
                  const percentOfFund = fundMetrics.totalFundValue > 0 ? (marketValue / fundMetrics.totalFundValue) * 100 : 0;
                  return (
                    <TableRow key={pos.id} className="hover:bg-slate-50/50">
                      <TableCell><div className="font-medium text-slate-800">{asset.symbol}</div><div className="text-xs text-slate-500 truncate max-w-[150px]">{asset.name}</div></TableCell>
                      <TableCell className="text-right font-medium text-slate-700">{formatNumber(pos.quantity, asset.asset_type === 'CRYPTO' ? 4 : (asset.asset_type === 'OPTION' ? 2: 2))}</TableCell>
                      <TableCell className="text-right text-slate-600">{formatCurrency(pos.average_cost_basis)}</TableCell>
                      <TableCell className="text-right text-slate-600">{formatCurrency(asset.current_price)}</TableCell>
                      <TableCell className="text-right font-semibold text-slate-800">{formatCurrency(marketValue)}</TableCell>
                      <TableCell className={cn("text-right font-medium", unrealizedPandL >=0 ? 'text-green-600' : 'text-red-600')}>{formatCurrency(unrealizedPandL, true)}</TableCell>
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
          {fund.transactions.length > 0 ? (
            <Table>
              <TableHeader><TableRow className="hover:bg-transparent"><TableHead>Date</TableHead><TableHead>Type</TableHead><TableHead>Asset</TableHead><TableHead className="text-right">Qty</TableHead><TableHead className="text-right">Price/Unit</TableHead><TableHead className="text-right">Total</TableHead><TableHead>Description</TableHead></TableRow></TableHeader>
              <TableBody>
                {fund.transactions.slice(0, 10).map(tx => {
                  const asset = tx.asset_id ? getAssetById(tx.asset_id, assets) : null;
                  return (
                    <TableRow key={tx.id} className="hover:bg-slate-50/50">
                      <TableCell className="text-xs text-slate-600">{formatDate(tx.transaction_date)}</TableCell>
                      <TableCell className="text-sm font-medium text-slate-700">{tx.transaction_type}</TableCell>
                      <TableCell className="text-sm text-slate-600">{asset?.symbol || 'N/A'}</TableCell>
                      <TableCell className="text-right text-sm text-slate-600">{tx.quantity !== undefined ? formatNumber(tx.quantity, asset?.asset_type === 'CRYPTO' ? 4 : 2) : 'N/A'}</TableCell>
                      <TableCell className="text-right text-sm text-slate-600">{tx.price_per_unit !== undefined ? formatCurrency(tx.price_per_unit) : 'N/A'}</TableCell>
                      <TableCell className={cn("text-right text-sm font-semibold", tx.total_amount >=0 ? "text-green-600" : "text-red-600")}>{formatCurrency(tx.total_amount)}</TableCell>
                      <TableCell className="text-xs text-slate-500 truncate max-w-[200px]">{tx.description || '-'}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <p className="text-sm text-slate-500 text-center py-6">No transactions recorded for this fund yet.</p>
          )}
          {fund.transactions.length > 10 && (
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
