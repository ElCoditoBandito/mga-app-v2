
// frontend/src/pages/PortfolioPage.tsx
import React, { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogClose,
} from '@/components/ui/dialog';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
// import { Skeleton } from '@/components/ui/skeleton';
import { DollarSign, TrendingUp, TrendingDown, Layers, Move, PlusCircle, Banknote, FilePieChart as FilePieChartIcon } from 'lucide-react'; // Renamed FilePieChart to avoid conflict
import { cn } from '@/lib/utils';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { toast } from 'sonner';
import LogStockTradeForm from '@/components/forms/LogStockTradeForm';
import type { StockTradeFormData } from '@/components/forms/LogStockTradeForm';
import LogOptionTradeForm from '@/components/forms/LogOptionTradeForm';
import type { OptionTradeFormData } from '@/components/forms/LogOptionTradeForm';

// --- Mock Data ---
interface Asset {
  id: string;
  symbol: string;
  name: string;
  current_price: number;
  asset_type?: 'STOCK' | 'OPTION' | 'CRYPTO'; // Added for allocation chart
}

interface Position {
  id: string;
  asset_id: string;
  quantity: number;
  average_cost_basis: number;
}

interface FundWithPositions {
  id: string;
  name: string;
  brokerage_cash_balance: number;
  positions: Position[];
  is_active: boolean;
}

interface PortfolioPageData {
  clubId: string;
  clubName: string;
  assets: Asset[];
  funds: FundWithPositions[];
  isAdmin: boolean;
}

const MOCK_ASSETS_STORE: Asset[] = [
  { id: 'asset1', symbol: 'AAPL', name: 'Apple Inc.', current_price: 175.50, asset_type: 'STOCK' },
  { id: 'asset2', symbol: 'MSFT', name: 'Microsoft Corp.', current_price: 340.20, asset_type: 'STOCK' },
  { id: 'asset3', symbol: 'GOOGL', name: 'Alphabet Inc. (A)', current_price: 150.75, asset_type: 'STOCK' },
  { id: 'asset4', symbol: 'AMZN', name: 'Amazon.com Inc.', current_price: 130.00, asset_type: 'STOCK' },
  { id: 'asset5', symbol: 'TSLA', name: 'Tesla Inc.', current_price: 250.00, asset_type: 'STOCK' },
  { id: 'asset6', symbol: 'BTC', name: 'Bitcoin', current_price: 60000, asset_type: 'CRYPTO' }, // Example Crypto
];

// Define mock funds data
const MOCK_FUNDS_WITH_POSITIONS_DATA: FundWithPositions[] = [
  { id: 'fundA', name: 'US Equities Fund', brokerage_cash_balance: 5000.25, positions: [
    { id: 'pos1', asset_id: 'asset1', quantity: 10, average_cost_basis: 150.00 },
    { id: 'pos2', asset_id: 'asset2', quantity: 5, average_cost_basis: 320.00 },
  ], is_active: true },
  { id: 'fundB', name: 'Global Growth Fund', brokerage_cash_balance: 10000.50, positions: [
    { id: 'pos3', asset_id: 'asset3', quantity: 20, average_cost_basis: 140.00 },
    { id: 'pos4', asset_id: 'asset4', quantity: 15, average_cost_basis: 120.00 },
  ], is_active: true },
  { id: 'fundC', name: 'Fixed Income & Crypto', brokerage_cash_balance: 2500.00, positions: [ // Ensure 'fundC' exists
    { id: 'pos5', asset_id: 'asset5', quantity: 8, average_cost_basis: 230.00 },
    // Note: The crypto position for asset6 is added later by existing code (lines 87-90)
  ], is_active: true }, // Changed to active to allow crypto position addition to be more meaningful for testing
   { id: 'fundD', name: 'Inactive Fund', brokerage_cash_balance: 100.00, positions: [], is_active: false },
];

// Initialize MOCK_PORTFOLIO_PAGE_DATA
const MOCK_PORTFOLIO_PAGE_DATA: PortfolioPageData = {
  clubId: 'club123',
  clubName: 'Eagle Investors Club',
  assets: [], // Will be populated by the line below
  funds: MOCK_FUNDS_WITH_POSITIONS_DATA,
  isAdmin: true,
};

MOCK_PORTFOLIO_PAGE_DATA.assets = MOCK_ASSETS_STORE; // Update existing mock data with new assets store
// Add a crypto position to one of the funds for chart variety
const fundCToUpdate = MOCK_PORTFOLIO_PAGE_DATA.funds.find(f => f.id === 'fundC');
if (fundCToUpdate) {
    fundCToUpdate.positions.push({ id: 'pos7', asset_id: 'asset6', quantity: 0.1, average_cost_basis: 55000 });
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

const getAssetById = (assetId: string, assets: Asset[]) => assets.find(a => a.id === assetId);

// --- Calculations ---
const calculatePortfolioMetrics = (funds: FundWithPositions[], assets: Asset[]) => {
  let totalAssetsMarketValue = 0; // Market value of non-cash assets
  let totalCostBasis = 0;
  let totalBrokerageCash = 0;

  funds.forEach(fund => {
    if (!fund.is_active) return;
    totalBrokerageCash += fund.brokerage_cash_balance;
    fund.positions.forEach(pos => {
      const asset = getAssetById(pos.asset_id, assets);
      if (asset) {
        const marketValue = pos.quantity * asset.current_price;
        const costBasis = pos.quantity * pos.average_cost_basis;
        totalAssetsMarketValue += marketValue;
        totalCostBasis += costBasis;
      }
    });
  });
  const totalMarketValue = totalAssetsMarketValue + totalBrokerageCash; // Overall total including cash
  const unrealizedPandL = totalAssetsMarketValue - totalCostBasis; // P&L on invested assets only

  return { totalMarketValue, totalCostBasis, unrealizedPandL, totalBrokerageCash, totalAssetsMarketValue };
};

const calculateFundMetrics = (fund: FundWithPositions, assets: Asset[]) => {
  let fundMarketValueAssets = 0;
  let fundCostBasis = 0;
  fund.positions.forEach(pos => {
    const asset = getAssetById(pos.asset_id, assets);
    if (asset) {
      fundMarketValueAssets += pos.quantity * asset.current_price;
      fundCostBasis += pos.quantity * pos.average_cost_basis;
    }
  });
  const fundTotalMarketValue = fundMarketValueAssets + fund.brokerage_cash_balance;
  const fundUnrealizedPandL = fundMarketValueAssets - fundCostBasis;
  return { fundTotalMarketValue, fundUnrealizedPandL, fundMarketValueAssets, fundCostBasis };
};

const calculateAssetAllocation = (activeFunds: FundWithPositions[], assets: Asset[], totalClubMarketValue: number) => {
    if (totalClubMarketValue === 0) return [];
    const allocation: { [key: string]: number } = { 'Cash': 0 };
    let totalCash = 0;

    activeFunds.forEach(fund => {
        totalCash += fund.brokerage_cash_balance;
        fund.positions.forEach(pos => {
            const asset = getAssetById(pos.asset_id, assets);
            if (asset) {
                const positionMarketValue = pos.quantity * asset.current_price;
                const assetType = asset.asset_type || 'Other Stocks'; // Default if no type
                allocation[assetType] = (allocation[assetType] || 0) + positionMarketValue;
            }
        });
    });
    allocation['Cash'] = totalCash;

    return Object.entries(allocation).map(([name, value]) => ({
        name,
        value,
        percentage: totalClubMarketValue > 0 ? (value / totalClubMarketValue) * 100 : 0,
    })).filter(item => item.value > 0); // Only include types with value
};

// Define colors for Pie Chart
const PIE_CHART_COLORS = ['#2563EB', '#34D399', '#F59E0B', '#EC4899', '#8B5CF6', '#6366F1', '#10B981'];

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: {
      name: string;
      value: number;
      percentage: number;
    }
  }>;
}

const CustomPieChartTooltip = ({ active, payload }: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-3 shadow-lg rounded-lg border border-slate-200">
        <p className="text-sm font-medium text-slate-800">{data.name}</p>
        <p className="text-xs text-slate-500">
          Value: <span className="font-semibold text-blue-600">{formatCurrency(data.value)}</span>
        </p>
        <p className="text-xs text-slate-500">
          Percentage: <span className="font-semibold text-blue-600">{data.percentage.toFixed(2)}%</span>
        </p>
      </div>
    );
  }
  return null;
};


// --- Inter-Fund Transfer Modal (collapsed for brevity, no changes from previous) --- 
interface TransferConfirmDetails {
  positionId: string;
  assetId: string;
  sourceFundId: string;
  targetFundId: string;
  quantity: number;
  transferDate: string;
  notes: string;
}

interface InterFundTransferModalProps {
  position: Position;
  asset: Asset;
  sourceFund: FundWithPositions;
  availableTargetFunds: FundWithPositions[];
  onTransferConfirm: (details: TransferConfirmDetails) => void;
}
const InterFundTransferModal: React.FC<InterFundTransferModalProps> = ({ onTransferConfirm, ...props }) => {
    // ... same implementation as before
    const {position, asset, sourceFund, availableTargetFunds} = props;
    const [targetFundId, setTargetFundId] = useState<string>('');
    const [quantityToTransfer, setQuantityToTransfer] = useState<number>(position.quantity);
    const [transferDate, setTransferDate] = useState<string>(new Date().toISOString().split('T')[0]);
    const [notes, setNotes] = useState('');

    const handleSubmit = () => {
        if (!targetFundId || quantityToTransfer <= 0 || quantityToTransfer > position.quantity) { alert("Please select a target fund and ensure quantity is valid."); return; }
        onTransferConfirm({ positionId: position.id, assetId: asset.id, sourceFundId: sourceFund.id, targetFundId, quantity: quantityToTransfer, transferDate, notes });
    };
    return (
        <DialogContent className="sm:max-w-md bg-white">
            <DialogHeader><DialogTitle className="text-slate-800">Inter-Fund Position Transfer</DialogTitle><DialogDescription>Transferring {asset.symbol} ({asset.name}) from {sourceFund.name}.</DialogDescription></DialogHeader>
            <div className="space-y-4 py-2">
                <div><Label htmlFor="targetFund" className="text-slate-700">Target Fund</Label><Select onValueChange={setTargetFundId} value={targetFundId} required><SelectTrigger id="targetFund" className="mt-1 w-full border-slate-300 focus:border-blue-500 focus:ring-blue-500"><SelectValue placeholder="Select target fund..." /></SelectTrigger><SelectContent>{availableTargetFunds.map(fund => (<SelectItem key={fund.id} value={fund.id}>{fund.name}</SelectItem>))}</SelectContent></Select></div>
                <div><Label htmlFor="quantityToTransfer" className="text-slate-700">Quantity to Transfer (Max: {position.quantity})</Label><Input id="quantityToTransfer" type="number" value={quantityToTransfer} onChange={(e) => setQuantityToTransfer(parseFloat(e.target.value) || 0)} max={position.quantity} min="0.000001" step="any" className="mt-1 border-slate-300 focus:border-blue-500 focus:ring-blue-500"/></div>
                <div><Label htmlFor="transferDate" className="text-slate-700">Transfer Date</Label><Input id="transferDate" type="date" value={transferDate} onChange={(e) => setTransferDate(e.target.value)} className="mt-1 border-slate-300 focus:border-blue-500 focus:ring-blue-500"/></div>
                <div><Label htmlFor="notes" className="text-slate-700">Reason/Notes (Optional)</Label><Input id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} className="mt-1 border-slate-300 focus:border-blue-500 focus:ring-blue-500"/></div>
            </div>
            <DialogFooter className="mt-6"><DialogClose asChild><Button type="button" variant="outline">Cancel</Button></DialogClose><Button onClick={handleSubmit} className="bg-blue-600 hover:bg-blue-700"><Move className="mr-2 h-4 w-4" /> Confirm Transfer</Button></DialogFooter>
        </DialogContent>
    );
};

// --- Main Portfolio Page Component --- 
const PortfolioPage = () => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { clubId: _clubId } = useParams<{ clubId: string }>();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [pageData, _setPageData] = useState<PortfolioPageData>(MOCK_PORTFOLIO_PAGE_DATA);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [isLoading, _setIsLoading] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [error, _setError] = useState<Error | null>(null);

  const [openTransferModal, setOpenTransferModal] = useState(false);
  const [transferDetails, setTransferDetails] = useState<Omit<InterFundTransferModalProps, 'onTransferConfirm' | 'availableTargetFunds'> | null>(null);
  
  // State for trade modals
  const [isLogStockTradeModalOpen, setIsLogStockTradeModalOpen] = useState(false);
  const [isLogOptionTradeModalOpen, setIsLogOptionTradeModalOpen] = useState(false);
  const [selectedFundContextForTrade, setSelectedFundContextForTrade] = useState<{
    clubId: string | undefined,
    fundId: string,
    fundName: string
  } | null>(null);

  const overallMetrics = useMemo(() => {
    if (!pageData) return { totalMarketValue: 0, totalCostBasis: 0, unrealizedPandL: 0, totalBrokerageCash: 0, totalAssetsMarketValue: 0 };
    return calculatePortfolioMetrics(pageData.funds.filter(f => f.is_active), pageData.assets);
  }, [pageData]);

  const assetAllocationData = useMemo(() => {
    if (!pageData) return [];
    return calculateAssetAllocation(pageData.funds.filter(f => f.is_active), pageData.assets, overallMetrics.totalMarketValue);
  }, [pageData, overallMetrics.totalMarketValue]);

  const handleInitiateTransfer = (position: Position, asset: Asset, sourceFund: FundWithPositions) => {
    setTransferDetails({ position, asset, sourceFund });
    setOpenTransferModal(true);
  };
  
  // Handler for stock trade form submission
  async function handleLogStockTradeSubmit(formData: StockTradeFormData) {
    console.log('Stock trade form data:', formData);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    toast.success("Stock trade logged successfully");
    setIsLogStockTradeModalOpen(false);
    // Future: Refresh data
  }
  
  // Handler for option trade form submission
  async function handleLogOptionTradeSubmit(formData: OptionTradeFormData) {
    console.log('Option trade form data:', formData);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    toast.success("Option trade logged successfully");
    setIsLogOptionTradeModalOpen(false);
    // Future: Refresh data
  }

  const handleTransferConfirm = (details: TransferConfirmDetails) => {
    console.log('Transfer Confirmed:', details);
    setOpenTransferModal(false);
    setTransferDetails(null);
  };

  if (isLoading) { /* Skeleton */ }
  if (error || !pageData) { /* Error */ }

  const { funds, assets, isAdmin } = pageData;
  const activeFunds = funds.filter(f => f.is_active);

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Club Portfolio Overview</h1>
        <p className="text-slate-600">View all investment positions and understand the club's overall investment landscape.</p>
      </header>

      {/* Section 1: Overall Club Portfolio Summary Metrics */}
      <Card className="bg-white border-slate-200/75 shadow-sm">
        <CardHeader><CardTitle className="text-lg font-medium text-slate-800">Overall Club Summary</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { title: 'Total Club Market Value', value: overallMetrics.totalMarketValue, icon: DollarSign, id: 'tmv' }, // Renamed for clarity
              { title: 'Total Assets Market Value', value: overallMetrics.totalAssetsMarketValue, icon: Layers, id: 'tamv' }, // Value of non-cash assets
              { title: 'Overall Unrealized P&L', value: overallMetrics.unrealizedPandL, icon: overallMetrics.unrealizedPandL >= 0 ? TrendingUp : TrendingDown, colorClass: overallMetrics.unrealizedPandL >= 0 ? 'text-green-600' : 'text-red-600', id: 'upl' },
              { title: 'Total Brokerage Cash', value: overallMetrics.totalBrokerageCash, icon: Banknote, id: 'tbc' },
            ].map(metric => (
              <div key={metric.id} className="p-3 rounded-lg bg-slate-50/70 border border-slate-200/60">
                <div className="flex items-center justify-between mb-0.5"><h3 className="text-[0.7rem] font-medium text-slate-500 uppercase tracking-wider">{metric.title}</h3><metric.icon className={cn("h-4 w-4", metric.colorClass || 'text-slate-400')} /></div>
                <p className={cn("text-xl font-bold text-slate-900", metric.colorClass)}>{formatCurrency(metric.value, metric.id === 'upl')}</p>
              </div>
            ))}
        </CardContent>
      </Card>

      {/* Section 2: Asset Allocation (Club-Wide) */}
      <Card className="bg-white border-slate-200/75 shadow-sm">
        <CardHeader>
            <CardTitle className="text-lg font-medium text-slate-800">Club Asset Allocation</CardTitle>
            <CardDescription className="text-sm text-slate-500">Breakdown of assets by type across the entire club.</CardDescription>
        </CardHeader>
        <CardContent className="h-72 md:h-80 p-4">
          {assetAllocationData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={assetAllocationData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  // label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={window.innerWidth < 768 ? 60 : 100} // Smaller radius for mobile
                  innerRadius={window.innerWidth < 768 ? 30 : 50} // Donut chart
                  fill="#8884d8"
                  dataKey="value"
                  nameKey="name"
                  paddingAngle={2}
                >
                  {assetAllocationData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_CHART_COLORS[index % PIE_CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomPieChartTooltip />} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center h-full">
                <FilePieChartIcon className="h-12 w-12 text-slate-400 mb-3" />
                <p className="text-slate-500">No asset allocation data to display.</p>
                <p className="text-xs text-slate-400">This may be due to no active funds or positions.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Section 3: Fund-by-Fund Portfolio Breakdown (Accordion) - No changes, collapsed for brevity */}
      <div>
        <h2 className="text-xl font-semibold text-slate-800 tracking-tight mb-3">Fund Portfolios</h2>
        {activeFunds.length > 0 ? (
          <Accordion type="single" collapsible className="w-full space-y-3" defaultValue={`fund-accordion-${activeFunds[0].id}`}>
            {activeFunds.map((fund) => {
              const fundMetrics = calculateFundMetrics(fund, assets);
              return (
                <AccordionItem key={fund.id} value={`fund-accordion-${fund.id}`} className="bg-white border border-slate-200/75 shadow-sm rounded-lg hover:shadow-md transition-shadow">
                  <AccordionTrigger className="px-4 py-3 hover:bg-slate-50/80 rounded-t-lg">
                    <div className="flex-1 flex flex-col sm:flex-row justify-between items-start sm:items-center text-left">
                        <div>
                            <h3 className="text-md font-semibold text-blue-600 group-hover:text-blue-700">{fund.name}</h3>
                            <p className="text-xs text-slate-500 mt-0.5">
                                Market Value: <span className="font-medium text-slate-700">{formatCurrency(fundMetrics.fundTotalMarketValue)}</span> |
                                Brokerage Cash: <span className="font-medium text-slate-700">{formatCurrency(fund.brokerage_cash_balance)}</span> |
                                P&L: <span className={cn("font-medium", fundMetrics.fundUnrealizedPandL >= 0 ? 'text-green-600' : 'text-red-600')}>{formatCurrency(fundMetrics.fundUnrealizedPandL, true)}</span>
                            </p>
                        </div>
                        {isAdmin && (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                size="sm"
                                variant="outline"
                                className="mt-2 sm:mt-0 bg-white hover:bg-slate-100 text-xs"
                                onClick={(e) => { e.stopPropagation(); }}
                              >
                                <PlusCircle className="mr-1.5 h-3.5 w-3.5" /> Log Trade for Fund
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-48">
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedFundContextForTrade({
                                    clubId: pageData.clubId,
                                    fundId: fund.id,
                                    fundName: fund.name
                                  });
                                  setIsLogStockTradeModalOpen(true);
                                }}
                              >
                                Stock Trade
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedFundContextForTrade({
                                    clubId: pageData.clubId,
                                    fundId: fund.id,
                                    fundName: fund.name
                                  });
                                  setIsLogOptionTradeModalOpen(true);
                                }}
                              >
                                Option Trade
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="px-4 py-3 border-t border-slate-200/75">
                    {fund.positions.length > 0 ? (
                      <Table>
                        <TableHeader><TableRow className="hover:bg-transparent"><TableHead>Asset</TableHead><TableHead className="text-right">Qty</TableHead><TableHead className="text-right">Avg. Cost</TableHead><TableHead className="text-right">Current Price</TableHead><TableHead className="text-right">Market Value</TableHead><TableHead className="text-right">Unreal. P&L</TableHead><TableHead className="text-right">% of Fund</TableHead>{isAdmin && <TableHead className="text-center w-[100px]">Actions</TableHead>}</TableRow></TableHeader>
                        <TableBody>
                          {fund.positions.map((pos) => {
                            const asset = getAssetById(pos.asset_id, assets);
                            if (!asset) return <TableRow key={pos.id}><TableCell colSpan={isAdmin ? 8 : 7}>Asset not found</TableCell></TableRow>;                            
                            const positionMarketValue = pos.quantity * asset.current_price;
                            const positionCostBasis = pos.quantity * pos.average_cost_basis;
                            const positionUnrealizedPandL = positionMarketValue - positionCostBasis;
                            const percentOfFund = fundMetrics.fundTotalMarketValue > 0 ? (positionMarketValue / fundMetrics.fundTotalMarketValue) * 100 : 0;
                            return (
                              <TableRow key={pos.id} className="hover:bg-slate-50/50">
                                <TableCell><div className="font-medium text-slate-800">{asset.symbol}</div><div className="text-xs text-slate-500 truncate max-w-[150px]">{asset.name}</div></TableCell>
                                <TableCell className="text-right font-medium text-slate-700">{formatNumber(pos.quantity, asset.asset_type === 'CRYPTO' ? 4 : 2)}</TableCell>
                                <TableCell className="text-right text-slate-600">{formatCurrency(pos.average_cost_basis)}</TableCell>
                                <TableCell className="text-right text-slate-600">{formatCurrency(asset.current_price)}</TableCell>
                                <TableCell className="text-right font-semibold text-slate-800">{formatCurrency(positionMarketValue)}</TableCell>
                                <TableCell className={cn("text-right font-medium", positionUnrealizedPandL >= 0 ? 'text-green-600' : 'text-red-600')}>{formatCurrency(positionUnrealizedPandL, true)}</TableCell>
                                <TableCell className="text-right text-slate-600">{formatNumber(percentOfFund)}%</TableCell>
                                {isAdmin && (<TableCell className="text-center"><Button variant="ghost" size="icon" className="h-8 w-8 text-slate-500 hover:text-blue-600 hover:bg-blue-100/50" onClick={() => handleInitiateTransfer(pos, asset, fund)}><Move className="h-4 w-4" /><span className="sr-only">Transfer</span></Button></TableCell>)}
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    ) : (<p className="text-sm text-slate-500 text-center py-4">No positions in this fund yet.</p>)}
                  </AccordionContent>
                </AccordionItem>
              );
            })}
          </Accordion>
        ) : (
          <Card className="bg-white border-slate-200/75 shadow-sm"><CardContent className="p-6 text-center"><Layers className="h-12 w-12 text-slate-400 mx-auto mb-3" /><CardTitle className="text-slate-700">No Active Funds</CardTitle><CardDescription className="text-slate-500 mt-1">There are no active funds to display portfolio information for.</CardDescription></CardContent></Card>
        )}
      </div>

      {transferDetails && (<Dialog open={openTransferModal} onOpenChange={(isOpen) => { if(!isOpen) setTransferDetails(null); setOpenTransferModal(isOpen); }}><InterFundTransferModal {...transferDetails} availableTargetFunds={activeFunds.filter(f => f.id !== transferDetails.sourceFund.id)} onTransferConfirm={handleTransferConfirm}/></Dialog>)}

      {/* Stock Trade Modal */}
      <Dialog open={isLogStockTradeModalOpen} onOpenChange={setIsLogStockTradeModalOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Log Stock Trade for {selectedFundContextForTrade?.fundName}</DialogTitle>
          </DialogHeader>
          {selectedFundContextForTrade && (
            <LogStockTradeForm
              funds={[{ id: selectedFundContextForTrade.fundId, name: selectedFundContextForTrade.fundName }]}
              initialFundId={selectedFundContextForTrade.fundId}
              onSubmit={handleLogStockTradeSubmit}
              onCancel={() => setIsLogStockTradeModalOpen(false)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Option Trade Modal */}
      <Dialog open={isLogOptionTradeModalOpen} onOpenChange={setIsLogOptionTradeModalOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Log Option Trade for {selectedFundContextForTrade?.fundName}</DialogTitle>
          </DialogHeader>
          {selectedFundContextForTrade && (
            <LogOptionTradeForm
              funds={[{ id: selectedFundContextForTrade.fundId, name: selectedFundContextForTrade.fundName }]}
              initialFundId={selectedFundContextForTrade.fundId}
              onSubmit={handleLogOptionTradeSubmit}
              onCancel={() => setIsLogOptionTradeModalOpen(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PortfolioPage;
