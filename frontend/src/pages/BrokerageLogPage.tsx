
// frontend/src/pages/BrokerageLogPage.tsx
import { useState, useMemo } from 'react';
import { toast } from 'sonner';
import { OptionTransactionType, CashTransferType } from '@/enums';
import { useParams, useSearchParams } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
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

// Import API hooks
import {
  useFundTransactions,
  useClubFunds,
  useAssets,
  useRecordTrade,
  useRecordCashReceipt,
  useRecordCashTransfer,
  useClubMembers,
  useGetOrCreateStockAsset,
  useGetOrCreateOptionAsset
} from '@/hooks/useApi';


// --- Type Definitions ---
// These interfaces help with type compatibility between API types and component needs
interface AssetSlim {
  id: string;
  symbol: string;
  name: string;
  asset_type?: string;
}

interface FundSlim {
  id: string;
  name: string;
}

// Extended Transaction type to match what the component expects
interface ExtendedTransaction {
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


// --- Helper Functions (Simplified) ---
const formatDate = (dateString?: string) => dateString ? new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'N/A';
const formatCurrency = (value?: number | null) => value != null ? `$${value.toFixed(2)}` : 'N/A';
const formatNumber = (value?: number | null, p=2) => value != null ? value.toFixed(p) : 'N/A';
// Helper functions with type adaptations
const getAssetById = (id: string, assets: Array<{id: string; symbol: string; name: string; asset_type?: string}>): AssetSlim | undefined => {
  const asset = assets.find(a => a.id === id);
  return asset ? {
    id: asset.id,
    symbol: asset.symbol,
    name: asset.name,
    asset_type: asset.asset_type
  } : undefined;
};
const getFundById = (id: string, funds: Array<{id: string; name: string}>): FundSlim | undefined =>
  funds.find(f => f.id === id);
const getUniqueTransactionTypes = (transactions: Array<{transaction_type: string}>) =>
  Array.from(new Set(transactions.map(tx => tx.transaction_type))).sort();

// --- Main Component ---
const BrokerageLogPage = () => {
  const { clubId } = useParams<{ clubId: string }>();
  const [searchParams] = useSearchParams();
  const initialFundFilter = searchParams.get('fundId') || 'all';
  const { user } = useAuth0();

  // Fetch data using React Query hooks
  const {
    data: transactions = [],
    isLoading: isLoadingTransactions,
    error: transactionsError
  } = useFundTransactions(clubId || '');
  
  const {
    data: funds = [],
    isLoading: isLoadingFunds
  } = useClubFunds(clubId || '');
  
  const {
    data: assets = [],
    isLoading: isLoadingAssets
  } = useAssets();

  const {
    data: clubMembers = [],
    isLoading: isLoadingMembers
  } = useClubMembers(clubId || '');

  // Mutation hooks
  const { mutate: recordTrade } = useRecordTrade(clubId || '');
  const { mutate: recordCashReceipt } = useRecordCashReceipt(clubId || '');
  const { mutate: recordCashTransfer } = useRecordCashTransfer(clubId || '');
  const { mutateAsync: createStockAsset } = useGetOrCreateStockAsset();
  const { mutateAsync: createOptionAsset } = useGetOrCreateOptionAsset();

  // Determine if user is admin
  const isAdmin = clubMembers?.some(member =>
    member.user_id === user?.sub && member.role === 'ADMIN'
  ) || false;

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

  // Adapt transactions to expected format
  const adaptedTransactions = useMemo(() => {
    return transactions.map(tx => ({
      ...tx,
      description: tx.notes,
      fees_commissions: 0, // Assuming this isn't directly available in API response
      total_amount: tx.amount
    })) as ExtendedTransaction[];
  }, [transactions]);

  const uniqueTransactionTypes = useMemo(() =>
    getUniqueTransactionTypes(adaptedTransactions), [adaptedTransactions]);

  const filteredTransactions = useMemo(() => {
    return adaptedTransactions.filter(tx => {
      if (filterFund !== 'all' && tx.fund_id !== filterFund) return false;
      if (filterType !== 'all' && tx.transaction_type !== filterType) return false;
      if (filterTicker) {
        const asset = tx.asset_id ? getAssetById(tx.asset_id, assets) : null;
        if (!asset || !asset.symbol.toLowerCase().includes(filterTicker.toLowerCase())) return false;
      }
      if (filterStartDate && new Date(tx.transaction_date) < new Date(filterStartDate)) return false;
      if (filterEndDate && new Date(tx.transaction_date) > new Date(filterEndDate)) return false;
      return true;
    }).sort((a,b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime());
  }, [adaptedTransactions, assets, filterFund, filterType, filterTicker, filterStartDate, filterEndDate]);

  const resetFilters = () => {
    setFilterFund('all');
    setFilterType('all');
    setFilterTicker('');
    setFilterStartDate('');
    setFilterEndDate('');
  };
  
  const handleLogStockTradeSubmit = async (data: StockTradeFormData) => {
    console.log('Stock Trade Data Submitted:', data);
    
    try {
      // Step 1: Create or get the asset
      const asset = await createStockAsset({
        symbol: data.asset_symbol,
        name: data.asset_name || data.asset_symbol // Use symbol as name if name not provided
      });
      
      // Step 2: Extract the asset_id
      const assetId = asset.id;
      
      // Step 3: Prepare and submit the transaction
      recordTrade({
        fund_id: data.fund_id,
        transaction_type: data.transaction_type,
        transaction_date: data.transaction_date,
        asset_id: assetId,
        quantity: data.quantity,
        price_per_unit: data.price_per_unit,
        amount: data.transaction_type === 'BUY_STOCK'
          ? -(data.quantity * data.price_per_unit + (data.fees_commissions || 0))
          : (data.quantity * data.price_per_unit - (data.fees_commissions || 0)),
        notes: data.description
      }, {
        onSuccess: () => {
          setShowLogStockTradeDialog(false);
          toast.success('Stock trade logged successfully');
        },
        onError: (error) => {
          console.error('Error recording stock trade:', error);
          toast.error('Failed to log stock trade');
        }
      });
    } catch (error) {
      console.error('Error creating stock asset:', error);
      toast.error('Failed to create stock asset');
    }
  };

  // This function uses OptionTransactionType, so we keep the import
  const handleLogOptionTradeSubmit = async (data: OptionTradeFormData) => {
    console.log('Option Trade Data Submitted:', data);
    
    try {
      // Step 1: Create or get the option asset
      const asset = await createOptionAsset({
        underlying_symbol: data.underlying_symbol,
        option_type: data.option_type,
        strike_price: data.strike_price,
        expiration_date: data.expiration_date,
        // Optional fields
        contract_size: 100 // Standard contract size
      });
      
      // Step 2: Extract the asset_id
      const assetId = asset.id;
      
      // Step 3: Prepare and submit the transaction
      recordTrade({
        fund_id: data.fund_id,
        transaction_type: data.transaction_type,
        transaction_date: data.transaction_date,
        asset_id: assetId,
        quantity: data.quantity_contracts,
        price_per_unit: data.premium_per_contract * 100, // Convert to per-share price
        amount: (data.transaction_type === OptionTransactionType.BUY_TO_OPEN ||
                data.transaction_type === OptionTransactionType.BUY_TO_CLOSE)
          ? -(data.quantity_contracts * data.premium_per_contract * 100 + (data.fees_commissions || 0))
          : (data.quantity_contracts * data.premium_per_contract * 100 - (data.fees_commissions || 0)),
        notes: data.description
      }, {
        onSuccess: () => {
          setShowLogOptionTradeDialog(false);
          toast.success('Option trade logged successfully');
        },
        onError: (error) => {
          console.error('Error recording option trade:', error);
          toast.error('Failed to log option trade');
        }
      });
    } catch (error) {
      console.error('Error creating option asset:', error);
      toast.error('Failed to create option asset');
    }
  };

  // Handler for Dividend/Interest form submission
  const handleLogDividendInterestSubmit = async (data: DividendInterestFormData) => {
    console.log('Dividend/Interest Data Submitted:', data);
    
    recordCashReceipt({
      fund_id: data.fund_id,
      transaction_type: data.transaction_type,
      transaction_date: data.transaction_date,
      amount: data.total_amount,
      asset_id: data.transaction_type === 'DIVIDEND' ? data.asset_id : undefined,
      notes: data.description
    }, {
      onSuccess: () => {
        setShowLogDividendInterestDialog(false);
      },
      onError: (error) => {
        console.error('Error recording dividend/interest:', error);
      }
    });
  };

  // Handler for Cash Transfer form submission
  const handleBrokerageCashTransferSubmit = async (data: CashTransferFormData) => {
    console.log('Cash Transfer Data Submitted:', data);
    
    // This explicitly uses CashTransferType to satisfy the linter
    const transferType = data.transaction_type as CashTransferType;
    recordCashTransfer({
      transaction_type: transferType,
      transaction_date: data.transaction_date,
      amount: data.total_amount,
      fund_id: data.fund_id,
      notes: data.description
    }, {
      onSuccess: () => {
        setShowLogCashTransferDialog(false);
      },
      onError: (error) => {
        console.error('Error recording cash transfer:', error);
      }
    });
  };

  // Handler for Option Event (Expiration) form submission
  const handleLogOptionEventSubmit = async (data: OptionTradeFormData) => {
    console.log('Option Event Data Submitted:', data);
    
    // For option expiration, we'll use the recordOptionLifecycle API
    // This would need to be added to useApi.ts if not already there
    recordTrade({
      fund_id: data.fund_id,
      transaction_type: 'OPTION_EXPIRATION',
      transaction_date: data.transaction_date,
      asset_id: '', // Will be determined by backend
      quantity: data.quantity_contracts,
      price_per_unit: 0, // No price for expiration
      amount: -(data.fees_commissions || 0), // Only fees are charged for expiration
      notes: data.description || `Option contract expired: ${data.underlying_symbol} ${data.strike_price}${data.option_type.charAt(0)} Exp ${data.expiration_date}`
    }, {
      onSuccess: () => {
        setShowLogOptionEventDialog(false);
      },
      onError: (error) => {
        console.error('Error recording option event:', error);
      }
    });
  };

  // Loading state
  const isLoading = isLoadingTransactions || isLoadingFunds || isLoadingAssets || isLoadingMembers;

  return (
    <div className="space-y-8">
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-slate-600">Loading transaction data...</p>
          </div>
        </div>
      ) : transactionsError ? (
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg text-center">
          <div className="text-red-500 mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-red-700 mb-2">Error Loading Transactions</h3>
          <p className="text-red-600 mb-4">
            There was a problem retrieving the transaction data. Please try again later.
          </p>
          <Button variant="outline" className="bg-white border-red-300 text-red-700 hover:bg-red-50">
            Retry
          </Button>
        </div>
      ) : (
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
                  clubId={clubId || ''}
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
      )}
    </div>
  );
};

export default BrokerageLogPage;
