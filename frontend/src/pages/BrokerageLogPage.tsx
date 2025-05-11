
// frontend/src/pages/BrokerageLogPage.tsx
import { useState, useMemo } from 'react';
import { OptionTransactionType, CashTransferType } from '@/enums';
import { useParams, useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogTrigger,
  // DialogClose, // Not always needed if form has its own cancel/submit close logic
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
// import { Skeleton } from '@/components/ui/skeleton'; // Assuming not actively used for now
import { PlusCircle, Download, Filter, Edit3 } from 'lucide-react';
import { cn } from '@/lib/utils';

// Import Forms
import LogStockTradeForm, { type StockTradeFormData } from '@/components/forms/LogStockTradeForm';
import LogOptionTradeForm, { type OptionTradeFormData } from '@/components/forms/LogOptionTradeForm';
import LogCashTransferForm, { type CashTransferFormData } from '@/components/forms/LogCashTransferForm';
import LogDividendInterestForm, { type DividendInterestFormData } from '@/components/forms/LogDividendInterestForm';


// --- Mock Data Structures (assuming these are defined elsewhere or similar to previous versions) ---
interface AssetSlim {
  id: string;
  symbol: string;
  name: string;
  asset_type?: 'STOCK' | 'OPTION' | 'CRYPTO';
}

interface FundSlim {
  id: string;
  name: string;
}

interface BrokerageTransaction {
  id: string;
  transaction_date: string;
  fund_id?: string;
  transaction_type: string;
  asset_id?: string;
  description?: string;
  quantity?: number;
  price_per_unit?: number;
  fees_commissions?: number;
  total_amount: number;
}

interface BrokerageLogPageData {
  clubId: string;
  clubName: string;
  transactions: BrokerageTransaction[];
  assets: AssetSlim[];
  funds: FundSlim[];
  isAdmin: boolean;
}

// --- Mock Data Generation (Simplified, ensure it matches what forms might need) ---
const MOCK_ASSETS_BROKERAGE: AssetSlim[] = [
  { id: 'asset1', symbol: 'AAPL', name: 'Apple Inc.', asset_type: 'STOCK' },
  { id: 'asset2', symbol: 'MSFT', name: 'Microsoft Corp.', asset_type: 'STOCK' },
  { id: 'assetOption1', symbol: 'AAPL251219C180', name: 'AAPL $180 CALL Exp 2025-12-19', asset_type: 'OPTION' },
];

const MOCK_FUNDS_SLIM: FundSlim[] = [
  { id: 'fundA', name: 'US Equities Fund' },
  { id: 'fundB', name: 'Global Growth Fund' },
];

const MOCK_BROKERAGE_LOG_DATA_STORE: { current: BrokerageLogPageData } = {
    current: {
        clubId: 'club123',
        clubName: 'Eagle Investors Club',
        isAdmin: true,
        assets: MOCK_ASSETS_BROKERAGE,
        funds: MOCK_FUNDS_SLIM,
        transactions: [
            { id: 'btx1', transaction_date: '2024-07-28', fund_id: 'fundA', transaction_type: 'BuyStock', asset_id: 'asset1', quantity: 10, price_per_unit: 175.00, fees_commissions: 0.50, total_amount: -1750.50, description: 'Bought AAPL shares' },
            { id: 'btx2', transaction_date: '2024-07-27', fund_id: 'fundB', transaction_type: 'SellOption', asset_id: 'assetOption1', quantity: 2, price_per_unit: 2.50, fees_commissions: 0.20, total_amount: 499.80, description: 'Sold AAPL Calls (STO)' },
        ],
    }
};


// --- Helper Functions (Simplified) ---
const formatDate = (dateString?: string) => dateString ? new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A';
const formatCurrency = (value?: number | null) => value != null ? `$${value.toFixed(2)}` : 'N/A';
const formatNumber = (value?: number | null, p=2) => value != null ? value.toFixed(p) : 'N/A';
const getAssetById = (id: string, assets: AssetSlim[]) => assets.find(a => a.id === id);
const getFundById = (id: string, funds: FundSlim[]) => funds.find(f => f.id === id);
const getUniqueTransactionTypes = (transactions: BrokerageTransaction[]) => Array.from(new Set(transactions.map(tx => tx.transaction_type))).sort();

// --- Main Component ---
const BrokerageLogPage = () => {
  const { clubId = 'club123' } = useParams<{ clubId: string }>(); // Default for mock
  const [searchParams] = useSearchParams();
  const initialFundFilter = searchParams.get('fundId') || 'all';

  const [pageData, setPageData] = useState<BrokerageLogPageData>({ ...MOCK_BROKERAGE_LOG_DATA_STORE.current, clubId: clubId });
  // Dialog states
  const [showLogStockTradeDialog, setShowLogStockTradeDialog] = useState(false);
  const [showLogOptionTradeDialog, setShowLogOptionTradeDialog] = useState(false);
  const [showLogDividendInterestDialog, setShowLogDividendInterestDialog] = useState(false);
  const [showLogCashTransferDialog, setShowLogCashTransferDialog] = useState(false);
  const [showLogOptionEventDialog, setShowLogOptionEventDialog] = useState(false);

  // Filters State
  const [filterFund, setFilterFund] = useState<string>(initialFundFilter);
  const [filterType, setFilterType] = useState<string>('all');
  const [filterTicker, setFilterTicker] = useState<string>('');
  const [filterStartDate, setFilterStartDate] = useState<string>('');
  const [filterEndDate, setFilterEndDate] = useState<string>('');

  const uniqueTransactionTypes = useMemo(() => getUniqueTransactionTypes(pageData.transactions), [pageData.transactions]);

  const filteredTransactions = useMemo(() => {
    return pageData.transactions.filter(tx => {
      if (filterFund !== 'all' && tx.fund_id !== filterFund) return false;
      if (filterType !== 'all' && tx.transaction_type !== filterType) return false;
      if (filterTicker) {
        const asset = tx.asset_id ? getAssetById(tx.asset_id, pageData.assets) : null;
        if (!asset || !asset.symbol.toLowerCase().includes(filterTicker.toLowerCase())) return false;
      }
      if (filterStartDate && new Date(tx.transaction_date) < new Date(filterStartDate)) return false;
      if (filterEndDate && new Date(tx.transaction_date) > new Date(filterEndDate)) return false;
      return true;
    }).sort((a,b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime());
  }, [pageData, filterFund, filterType, filterTicker, filterStartDate, filterEndDate]);

  const resetFilters = () => { /* ... */ }; // Keep existing reset logic

  const handleAddTransaction = (newTxData: Omit<BrokerageTransaction, 'id'>) => {
    const newTx: BrokerageTransaction = {
        ...newTxData,
        id: `btx${Math.random().toString(16).slice(2)}`,
    };
    setPageData(prev => ({
        ...prev,
        transactions: [newTx, ...prev.transactions] // Add to top and resort if needed
    }));
  };
  
  const handleLogStockTradeSubmit = async (data: StockTradeFormData) => {
    console.log('Stock Trade Data Submitted:', data);
    // Mock API call
    // In a real app, you'd transform `data` to match the backend's BrokerageTransaction schema
    const newTxData: Omit<BrokerageTransaction, 'id'> = {
        transaction_date: data.transaction_date,
        fund_id: data.fund_id,
        transaction_type: data.transaction_type, // This is 'BUY_STOCK' or 'SELL_STOCK'
        asset_id: pageData.assets.find(a => a.symbol === data.asset_symbol)?.id || `new_${data.asset_symbol}`, // Simplified asset handling
        description: data.description || `${data.transaction_type} ${data.asset_symbol}`,
        quantity: data.quantity,
        price_per_unit: data.price_per_unit,
        fees_commissions: data.fees_commissions,
        total_amount: (data.transaction_type === 'BUY_STOCK' ? -1 : 1) * (data.quantity * data.price_per_unit) + (data.transaction_type === 'BUY_STOCK' ? -(data.fees_commissions || 0) : (data.fees_commissions || 0)),
    };
    handleAddTransaction(newTxData);
    setShowLogStockTradeDialog(false); // Close dialog
  };

  const handleLogOptionTradeSubmit = async (data: OptionTradeFormData) => {
    console.log('Option Trade Data Submitted:', data);
     const newTxData: Omit<BrokerageTransaction, 'id'> = {
        transaction_date: data.transaction_date,
        fund_id: data.fund_id,
        transaction_type: data.transaction_type, // This is one of OptionTransactionType
        asset_id: pageData.assets.find(a => a.symbol === data.option_symbol_name)?.id || `new_opt_${data.underlying_symbol}`, // Simplified
        description: data.description || `${data.transaction_type} ${data.underlying_symbol} ${data.strike_price}${data.option_type.charAt(0)} Exp ${data.expiration_date}`,
        quantity: data.quantity_contracts, // Number of contracts
        price_per_unit: data.premium_per_contract, // Premium per share
        fees_commissions: data.fees_commissions,
        total_amount: (data.transaction_type === OptionTransactionType.BUY_TO_OPEN || data.transaction_type === OptionTransactionType.BUY_TO_CLOSE ? -1 : 1) * (data.quantity_contracts * data.premium_per_contract * 100) - (data.fees_commissions || 0),
    };
    handleAddTransaction(newTxData);
    setShowLogOptionTradeDialog(false); // Close dialog
  };

  // Handler for Dividend/Interest form submission
  const handleLogDividendInterestSubmit = async (data: DividendInterestFormData) => {
    console.log('Dividend/Interest Data Submitted:', data);
    // Mock API call
    await new Promise(resolve => setTimeout(resolve, 1000));

    const newTxData: Omit<BrokerageTransaction, 'id'> = {
      transaction_date: data.transaction_date,
      fund_id: data.fund_id,
      transaction_type: data.transaction_type, // 'DIVIDEND' or 'BROKERAGE_INTEREST'
      asset_id: data.transaction_type === 'DIVIDEND' ? data.asset_id : undefined,
      description: data.description || `${data.transaction_type === 'DIVIDEND' ? 'Dividend' : 'Brokerage Interest'} received`,
      total_amount: data.total_amount,
      fees_commissions: data.fees_commissions,
    };
    
    handleAddTransaction(newTxData);
    setShowLogDividendInterestDialog(false);
  };

  // Handler for Cash Transfer form submission
  const handleBrokerageCashTransferSubmit = async (data: CashTransferFormData) => {
    console.log('Cash Transfer Data Submitted:', data);
    // Mock API call
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Determine the correct transaction type based on source/destination
    let transactionType: string;
    if (data.transaction_type === CashTransferType.BANK_TO_BROKERAGE) {
      transactionType = 'BANK_TO_BROKERAGE';
    } else if (data.transaction_type === CashTransferType.BROKERAGE_TO_BANK) {
      transactionType = 'BROKERAGE_TO_BANK';
    } else {
      transactionType = 'INTERFUND_CASH_TRANSFER';
    }

    const newTxData: Omit<BrokerageTransaction, 'id'> = {
      transaction_date: data.transaction_date,
      fund_id: data.fund_id,
      transaction_type: transactionType,
      description: data.description || `Cash transfer: ${transactionType}`,
      total_amount: data.transaction_type === CashTransferType.BANK_TO_BROKERAGE ? data.total_amount : -data.total_amount,
    };
    
    handleAddTransaction(newTxData);
    setShowLogCashTransferDialog(false);
  };

  // Handler for Option Event (Expiration) form submission
  const handleLogOptionEventSubmit = async (data: OptionTradeFormData) => {
    console.log('Option Event Data Submitted:', data);
    // Mock API call
    await new Promise(resolve => setTimeout(resolve, 1000));

    // For option expiration events
    // Note: We're extending the existing LogOptionTradeForm to handle OPTION_EXPIRATION
    // The transaction_type will be one of the OptionTransactionType enum values
    const newTxData: Omit<BrokerageTransaction, 'id'> = {
      transaction_date: data.transaction_date,
      fund_id: data.fund_id,
      transaction_type: 'OPTION_EXPIRATION', // Override with the correct backend type
      // Use existing option asset or create a reference to a new one
      asset_id: pageData.assets.find(a => a.symbol === data.option_symbol_name)?.id || `new_opt_${data.underlying_symbol}`,
      description: data.description || `Option contract expired: ${data.underlying_symbol} ${data.strike_price}${data.option_type.charAt(0)} Exp ${data.expiration_date}`,
      quantity: data.quantity_contracts,
      fees_commissions: data.fees_commissions,
      total_amount: -(data.fees_commissions || 0), // Only fees are charged for expiration
    };
    
    handleAddTransaction(newTxData);
    setShowLogOptionEventDialog(false);
  };

  const { funds, assets, isAdmin } = pageData;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Brokerage Transactions Log</h1>

      {isAdmin && (
        <Card className="bg-white border-slate-200/75 shadow-sm">
          <CardHeader><CardTitle className="text-lg font-medium text-slate-800">Log New Transaction</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
            {/* Log Stock Trade */}
            <Dialog open={showLogStockTradeDialog} onOpenChange={setShowLogStockTradeDialog}>
              <DialogTrigger asChild>
                <Button variant="outline" className="bg-white justify-start text-left"><PlusCircle className="mr-2 h-4 w-4 text-blue-600"/>Log Stock Trade</Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-2xl bg-white p-6"> {/* Increased max-width */}
                {/* No DialogHeader needed here as form has its own */}
                <LogStockTradeForm
                  funds={funds}
                  onSubmit={handleLogStockTradeSubmit}
                  onCancel={() => setShowLogStockTradeDialog(false)}
                />
              </DialogContent>
            </Dialog>

            {/* Log Option Trade */}
            <Dialog open={showLogOptionTradeDialog} onOpenChange={setShowLogOptionTradeDialog}>
              <DialogTrigger asChild>
                <Button variant="outline" className="bg-white justify-start text-left"><PlusCircle className="mr-2 h-4 w-4 text-blue-600"/>Log Option Trade</Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-3xl bg-white p-6"> {/* Increased max-width */}
                <LogOptionTradeForm
                  funds={funds}
                  onSubmit={handleLogOptionTradeSubmit}
                  onCancel={() => setShowLogOptionTradeDialog(false)}
                />
              </DialogContent>
            </Dialog>
            
            {/* Dividend/Interest Dialog */}
            <Dialog open={showLogDividendInterestDialog} onOpenChange={setShowLogDividendInterestDialog}>
              <DialogTrigger asChild>
                <Button variant="outline" className="bg-white justify-start text-left">
                  <PlusCircle className="mr-2 h-4 w-4 text-blue-600"/>Record Dividend/Interest
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-2xl bg-white p-6">
                <LogDividendInterestForm
                  funds={funds}
                  assets={assets.filter(a => a.asset_type === 'STOCK').map(a => ({
                    id: a.id,
                    symbol: a.symbol,
                    name: a.name,
                    asset_type: a.asset_type || 'STOCK'
                  }))}
                  onSubmit={handleLogDividendInterestSubmit}
                  onCancel={() => setShowLogDividendInterestDialog(false)}
                />
              </DialogContent>
            </Dialog>

            {/* Cash Transfer Dialog */}
            <Dialog open={showLogCashTransferDialog} onOpenChange={setShowLogCashTransferDialog}>
              <DialogTrigger asChild>
                <Button variant="outline" className="bg-white justify-start text-left">
                  <PlusCircle className="mr-2 h-4 w-4 text-blue-600"/>Record Cash Transfer
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-2xl bg-white p-6">
                <LogCashTransferForm
                  clubId={pageData.clubId}
                  funds={funds}
                  onSubmit={handleBrokerageCashTransferSubmit}
                  onCancel={() => setShowLogCashTransferDialog(false)}
                />
              </DialogContent>
            </Dialog>

            {/* Option Event Dialog (using existing option trade form) */}
            <Dialog open={showLogOptionEventDialog} onOpenChange={setShowLogOptionEventDialog}>
              <DialogTrigger asChild>
                <Button variant="outline" className="bg-white justify-start text-left">
                  <PlusCircle className="mr-2 h-4 w-4 text-blue-600"/>Record Option Event
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-3xl bg-white p-6">
                <LogOptionTradeForm
                  funds={funds}
                  onSubmit={handleLogOptionEventSubmit}
                  onCancel={() => setShowLogOptionEventDialog(false)}
                />
              </DialogContent>
            </Dialog>

          </CardContent>
        </Card>
      )}

      {/* Transaction Table & Filters Card */}
      <Card className="bg-white border-slate-200/75 shadow-sm">
        <CardHeader>
            {/* ... existing filter UI ... */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <CardTitle className="text-lg font-medium text-slate-800">All Brokerage Transactions</CardTitle>
                    <CardDescription className="text-sm text-slate-600">View and filter all recorded brokerage activities.</CardDescription>
                </div>
                <Button variant="outline" size="sm" className="bg-white self-start md:self-center"><Download className="mr-2 h-4 w-4"/> Export Transactions</Button>
            </div>
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 items-end">
                <div><Label htmlFor="filterFund" className="text-xs">Fund</Label><Select value={filterFund} onValueChange={setFilterFund}><SelectTrigger id="filterFund" className="h-9 text-sm"><SelectValue/></SelectTrigger><SelectContent><SelectItem value="all">All Funds</SelectItem>{funds.map(f => <SelectItem key={f.id} value={f.id}>{f.name}</SelectItem>)}</SelectContent></Select></div>
                <div><Label htmlFor="filterType" className="text-xs">Type</Label><Select value={filterType} onValueChange={setFilterType}><SelectTrigger id="filterType" className="h-9 text-sm"><SelectValue/></SelectTrigger><SelectContent><SelectItem value="all">All Types</SelectItem>{uniqueTransactionTypes.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent></Select></div>
                <div><Label htmlFor="filterTicker" className="text-xs">Ticker</Label><Input id="filterTicker" value={filterTicker} onChange={e=>setFilterTicker(e.target.value)} placeholder="e.g. AAPL" className="h-9 text-sm"/></div>
                <div><Label htmlFor="filterStartDate" className="text-xs">Start Date</Label><Input id="filterStartDate" type="date" value={filterStartDate} onChange={e=>setFilterStartDate(e.target.value)} className="h-9 text-sm"/></div>
                <div><Label htmlFor="filterEndDate" className="text-xs">End Date</Label><Input id="filterEndDate" type="date" value={filterEndDate} onChange={e=>setFilterEndDate(e.target.value)} className="h-9 text-sm"/></div>
                <Button onClick={resetFilters} variant="ghost" className="h-9 text-sm text-blue-600 hover:text-blue-700 lg:col-start-6"><Filter className="mr-1.5 h-3.5 w-3.5"/>Reset Filters</Button>
            </div>
        </CardHeader>
        <CardContent className="p-0">
          {filteredTransactions.length > 0 ? (
            <Table>
              {/* ... Table structure ... */}
              <TableHeader><TableRow className="hover:bg-transparent text-xs"><TableHead>Date</TableHead><TableHead>Fund</TableHead><TableHead>Type</TableHead><TableHead>Asset</TableHead><TableHead>Description</TableHead><TableHead className="text-right">Qty</TableHead><TableHead className="text-right">Price/Unit</TableHead><TableHead className="text-right">Fees</TableHead><TableHead className="text-right">Total</TableHead>{isAdmin && <TableHead className="w-[50px]"></TableHead>}</TableRow></TableHeader>
              <TableBody>
                {filteredTransactions.map(tx => {
                  const asset = tx.asset_id ? getAssetById(tx.asset_id, assets) : null;
                  const fund = tx.fund_id ? getFundById(tx.fund_id, funds) : null;
                  return (
                    <TableRow key={tx.id} className="hover:bg-slate-50/50 text-sm">
                      <TableCell className="text-slate-600">{formatDate(tx.transaction_date)}</TableCell>
                      <TableCell className="text-slate-600">{fund?.name || 'N/A'}</TableCell>
                      <TableCell className="font-medium text-slate-700">{tx.transaction_type}</TableCell>
                      <TableCell className="text-slate-600">{asset?.symbol || 'N/A'}</TableCell>
                      <TableCell className="text-xs text-slate-500 truncate max-w-[150px]" title={tx.description}>{tx.description || '-'}</TableCell>
                      <TableCell className="text-right text-slate-600">{tx.quantity !== undefined ? formatNumber(tx.quantity, asset?.asset_type === 'CRYPTO' ? 4 : 2) : '-'}</TableCell>
                      <TableCell className="text-right text-slate-600">{tx.price_per_unit !== undefined ? formatCurrency(tx.price_per_unit) : '-'}</TableCell>
                      <TableCell className="text-right text-slate-600">{tx.fees_commissions !== undefined ? formatCurrency(tx.fees_commissions) : '-'}</TableCell>
                      <TableCell className={cn("text-right font-semibold", tx.total_amount >= 0 ? 'text-green-600' : 'text-red-600')}>{formatCurrency(tx.total_amount)}</TableCell>
                      {isAdmin && <TableCell className="text-center"><Button variant="ghost" size="icon" className="h-7 w-7 text-slate-500 hover:text-blue-600"><Edit3 className="h-4 w-4"/><span className="sr-only">Edit</span></Button></TableCell>}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <p className="text-center py-10 text-slate-500">No brokerage transactions match the current filters, or none recorded yet.</p>
          )}
        </CardContent>
        {filteredTransactions.length > 15 && <CardFooter className="pt-4 border-t"><p className="text-xs text-slate-500">Displaying first {filteredTransactions.length} transactions. Consider refining filters for large datasets.</p></CardFooter>}
      </Card>
    </div>
  );
};

export default BrokerageLogPage;
