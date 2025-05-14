
// frontend/src/components/forms/LogStockTradeForm.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'; // Assuming npx shadcn-ui@latest add radio-group
import { CardDescription, CardHeader, CardTitle } from '@/components/ui/card'; // For layout if used directly
import { AlertCircle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { TransactionType } from '@/enums';

// --- Mock Data Structures (align with backend Pydantic schemas if possible) ---
interface FundSlim {
  id: string;
  name: string;
}

// Based on TransactionCreateTrade and AssetCreateStock
export interface StockTradeFormData {
  fund_id: string;            // required
  transaction_type: string;   // required - using TransactionType.BUY_STOCK or TransactionType.SELL_STOCK
  asset_symbol: string;       // required (for AssetCreateStock or matching existing)
  asset_name?: string;        // optional (for AssetCreateStock)
  transaction_date: string;   // required, ISO format
  quantity: number;           // required, positive
  price_per_unit: number;   // required, positive
  fees_commissions?: number;  // optional, defaults to 0
  description?: string;       // optional
}

interface LogStockTradeFormProps {
  funds: FundSlim[]; // List of funds to assign the trade to
  initialFundId?: string; // Pre-select fund if form opened from specific fund context
  onSubmit: (data: StockTradeFormData) => Promise<void>; // Async to allow for API call indication
  onCancel?: () => void;
  // We might add existing assets later for lookup
}

const LogStockTradeForm: React.FC<LogStockTradeFormProps> = ({
  funds,
  initialFundId,
  onSubmit,
  onCancel,
}) => {
  const [fundId, setFundId] = useState<string>(initialFundId || (funds.length > 0 ? funds[0].id : ''));
  const [transactionType, setTransactionType] = useState<string>(TransactionType.BUY_STOCK);
  const [assetSymbol, setAssetSymbol] = useState('');
  const [assetName, setAssetName] = useState('');
  const [transactionDate, setTransactionDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [quantity, setQuantity] = useState<string>(''); // Store as string for input control
  const [pricePerUnit, setPricePerUnit] = useState<string>(''); // Store as string
  const [feesCommissions, setFeesCommissions] = useState<string>('0'); // Store as string
  const [description, setDescription] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calculatedTotal = useMemo(() => {
    const numQuantity = parseFloat(quantity);
    const numPrice = parseFloat(pricePerUnit);
    const numFees = parseFloat(feesCommissions) || 0;

    if (isNaN(numQuantity) || isNaN(numPrice) || numQuantity <= 0 || numPrice <= 0) {
      return null;
    }
    const baseAmount = numQuantity * numPrice;
    if (transactionType === TransactionType.BUY_STOCK) {
      return baseAmount + numFees;
    } else { // SELL_STOCK
      return baseAmount - numFees;
    }
  }, [quantity, pricePerUnit, feesCommissions, transactionType]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const numQuantity = parseFloat(quantity);
    const numPrice = parseFloat(pricePerUnit);
    const numFees = parseFloat(feesCommissions) || 0;

    if (!fundId) { setError('Fund assignment is required.'); return; }
    if (!assetSymbol.trim()) { setError('Ticker Symbol is required.'); return; }
    if (isNaN(numQuantity) || numQuantity <= 0) { setError('Valid quantity is required.'); return; }
    if (isNaN(numPrice) || numPrice <= 0) { setError('Valid price per share is required.'); return; }
    if (isNaN(numFees) || numFees < 0) { setError('Fees/Commissions cannot be negative.'); return; }
    
    const formData: StockTradeFormData = {
      fund_id: fundId,
      transaction_type: transactionType,
      asset_symbol: assetSymbol.toUpperCase().trim(),
      asset_name: assetName.trim() || undefined,
      transaction_date: transactionDate,
      quantity: numQuantity,
      price_per_unit: numPrice,
      fees_commissions: numFees,
      description: description.trim() || undefined,
    };

    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      // Optionally reset form here if not unmounted by parent
    } catch (submissionError: unknown) {
      const errorMessage =
        submissionError && typeof submissionError === 'object' && 'message' in submissionError
          ? String(submissionError.message)
          : 'Failed to save trade. Please try again.';
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Effect to update fundId if initialFundId changes and it's a valid fund
  useEffect(() => {
    if (initialFundId && funds.find(f => f.id === initialFundId)) {
        setFundId(initialFundId);
    } else if (funds.length > 0 && !initialFundId) {
        setFundId(funds[0].id); // Default to first fund if no initial one is provided
    }
  }, [initialFundId, funds]);


  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <CardHeader className="px-0 pt-0">
        <CardTitle className="text-xl font-semibold text-slate-800">Log Stock Trade</CardTitle>
        <CardDescription className="text-sm text-slate-600">
          Manually enter a stock purchase or sale for a specific fund.
        </CardDescription>
      </CardHeader>

      {error && (
        <div className="p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700 flex items-start">
          <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
          <div>
            <span className="font-medium">Error:</span> {error}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
        {/* Fund Assignment */}
        <div className="md:col-span-2">
          <Label htmlFor="fundId" className="font-medium text-slate-700">Assign to Fund <span className="text-red-500">*</span></Label>
          <Select value={fundId} onValueChange={setFundId} required>
            <SelectTrigger id="fundId" className="mt-1 w-full border-slate-300 focus:border-blue-500 focus:ring-blue-500">
              <SelectValue placeholder="Select a fund..." />
            </SelectTrigger>
            <SelectContent>
              {funds.length > 0 ? (
                funds.map(fund => <SelectItem key={fund.id} value={fund.id}>{fund.name}</SelectItem>)
              ) : (
                <SelectItem value="" disabled>No funds available</SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>

        {/* Transaction Type */}
        <div className="md:col-span-2">
          <Label className="font-medium text-slate-700">Trade Type <span className="text-red-500">*</span></Label>
          <RadioGroup
            value={transactionType}
            onValueChange={(value: string) => setTransactionType(value)}
            className="mt-2 flex space-x-4"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value={TransactionType.BUY_STOCK} id="buy_stock" />
              <Label htmlFor="buy_stock" className="font-normal text-slate-700 cursor-pointer">Buy Stock</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value={TransactionType.SELL_STOCK} id="sell_stock" />
              <Label htmlFor="sell_stock" className="font-normal text-slate-700 cursor-pointer">Sell Stock</Label>
            </div>
          </RadioGroup>
        </div>

        {/* Asset Details */}
        <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4 border-t border-slate-200 pt-4 mt-2">
            <div>
                <Label htmlFor="assetSymbol" className="font-medium text-slate-700">Ticker Symbol <span className="text-red-500">*</span></Label>
                <Input id="assetSymbol" value={assetSymbol} onChange={(e) => setAssetSymbol(e.target.value)} placeholder="e.g., AAPL" required className="mt-1" />
            </div>
            <div>
                <Label htmlFor="assetName" className="font-medium text-slate-700">Company Name</Label>
                <Input id="assetName" value={assetName} onChange={(e) => setAssetName(e.target.value)} placeholder="e.g., Apple Inc." className="mt-1" />
                <p className="text-xs text-slate-500 mt-1 flex items-start">
                    <Info className="h-3 w-3 mr-1 mt-0.5 flex-shrink-0" />
                    If the ticker is new, providing company name helps create a new asset entry.
                </p>
            </div>
        </div>


        {/* Trade Details */}
        <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4 border-t border-slate-200 pt-4 mt-2">
            <div>
                <Label htmlFor="transactionDate" className="font-medium text-slate-700">Transaction Date <span className="text-red-500">*</span></Label>
                <Input id="transactionDate" type="date" value={transactionDate} onChange={(e) => setTransactionDate(e.target.value)} required className="mt-1" />
            </div>
            <div>
                <Label htmlFor="quantity" className="font-medium text-slate-700">Quantity <span className="text-red-500">*</span></Label>
                <Input id="quantity" type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} placeholder="0.00" step="any" min="0.00000001" required className="mt-1" />
            </div>
            <div>
                <Label htmlFor="pricePerUnit" className="font-medium text-slate-700">Price per Share <span className="text-red-500">*</span></Label>
                <Input id="pricePerUnit" type="number" value={pricePerUnit} onChange={(e) => setPricePerUnit(e.target.value)} placeholder="0.00" step="any" min="0.00000001" required className="mt-1" />
            </div>
            <div className="md:col-span-1">
                <Label htmlFor="feesCommissions" className="font-medium text-slate-700">Fees/Commissions</Label>
                <Input id="feesCommissions" type="number" value={feesCommissions} onChange={(e) => setFeesCommissions(e.target.value)} placeholder="0.00" step="any" min="0" className="mt-1" />
            </div>
             {/* Calculated Display */}
            <div className="md:col-span-2 flex flex-col justify-end">
                <Label className="font-medium text-slate-700">Total Cost / Proceeds</Label>
                <div className={cn(
                    "mt-1 p-2 rounded-md text-lg font-semibold h-[38px] flex items-center",
                    calculatedTotal === null ? "bg-slate-100 text-slate-500 italic" : "bg-blue-50 border border-blue-200 text-blue-700"
                )}>
                    {calculatedTotal !== null ? `$${calculatedTotal.toFixed(2)}` : 'Enter quantity & price'}
                </div>
            </div>
        </div>


        {/* Notes */}
        <div className="md:col-span-2 border-t border-slate-200 pt-4 mt-2">
          <Label htmlFor="description" className="font-medium text-slate-700">Description/Notes</Label>
          <Textarea id="description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional notes about the trade..." rows={2} className="mt-1" />
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200 mt-6">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
        )}
        <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={isSubmitting || !fundId || funds.length === 0}>
          {isSubmitting ? 'Saving Trade...' : 'Save Trade'}
        </Button>
      </div>
    </form>
  );
};

export default LogStockTradeForm;
