// frontend/src/components/forms/LogDividendInterestForm.tsx
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { TransactionType } from '@/enums';

// --- Data Structures ---
interface FundSlim {
  id: string;
  name: string;
}

interface AssetSlim {
  id: string;
  symbol: string;
  name: string;
  asset_type: string;
}

export interface DividendInterestFormData {
  transaction_type: string; // Using TransactionType.DIVIDEND or TransactionType.BROKERAGE_INTEREST
  transaction_date: string; // ISO format
  fund_id: string;
  asset_id?: string; // Required for DIVIDEND, null for BROKERAGE_INTEREST
  total_amount: number; // Gross amount
  fees_commissions?: number;
  description?: string;
}

interface LogDividendInterestFormProps {
  funds: FundSlim[];
  assets: AssetSlim[]; // Stock assets for dividend selection
  onSubmit: (data: DividendInterestFormData) => Promise<void>;
  onCancel?: () => void;
}

const LogDividendInterestForm: React.FC<LogDividendInterestFormProps> = ({
  funds,
  assets,
  onSubmit,
  onCancel,
}) => {
  const [transactionType, setTransactionType] = useState<string>(TransactionType.DIVIDEND);
  const [transactionDate, setTransactionDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [fundId, setFundId] = useState<string>(funds.length > 0 ? funds[0].id : '');
  const [assetId, setAssetId] = useState<string>('');
  const [totalAmount, setTotalAmount] = useState<string>('');
  const [feesCommissions, setFeesCommissions] = useState<string>('0.00');
  const [description, setDescription] = useState<string>('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter stock assets for dividend selection
  const stockAssets = assets.filter(asset => asset.asset_type === 'STOCK');

  // Reset asset selection when transaction type changes
  useEffect(() => {
    if (transactionType === TransactionType.BROKERAGE_INTEREST) {
      setAssetId('');
    } else if (transactionType === TransactionType.DIVIDEND && stockAssets.length > 0 && !assetId) {
      setAssetId(stockAssets[0].id);
    }
  }, [transactionType, stockAssets, assetId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const numTotalAmount = parseFloat(totalAmount);
    const numFeesCommissions = parseFloat(feesCommissions) || 0;

    // Validation
    if (!fundId) { setError('Fund assignment is required.'); return; }
    if (isNaN(numTotalAmount) || numTotalAmount <= 0) { setError('Valid positive amount is required.'); return; }
    if (transactionType === TransactionType.DIVIDEND && !assetId) { setError('Asset selection is required for dividends.'); return; }
    if (isNaN(numFeesCommissions) || numFeesCommissions < 0) { setError('Fees/Commissions cannot be negative.'); return; }

    const formData: DividendInterestFormData = {
      transaction_type: transactionType,
      transaction_date: transactionDate,
      fund_id: fundId,
      total_amount: numTotalAmount,
      fees_commissions: numFeesCommissions || undefined,
      description: description.trim() || undefined,
    };

    // Only include asset_id for DIVIDEND type
    if (transactionType === TransactionType.DIVIDEND) {
      formData.asset_id = assetId;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      // Reset form
      setTransactionType(TransactionType.DIVIDEND);
      setTransactionDate(new Date().toISOString().split('T')[0]);
      setFundId(funds.length > 0 ? funds[0].id : '');
      setAssetId(stockAssets.length > 0 ? stockAssets[0].id : '');
      setTotalAmount('');
      setFeesCommissions('0.00');
      setDescription('');
    } catch (submissionError: unknown) {
      setError(submissionError instanceof Error ? submissionError.message : 'Failed to record dividend/interest. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <CardHeader className="px-0 pt-0">
        <CardTitle className="text-xl font-semibold text-slate-800">Record Dividend/Interest</CardTitle>
        <CardDescription className="text-sm text-slate-600">
          Record dividend payments from stocks or interest earned on brokerage cash.
        </CardDescription>
      </CardHeader>

      {error && (
        <div className="p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700 flex items-start">
          <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
          <div><span className="font-medium">Error:</span> {error}</div>
        </div>
      )}

      <div className="space-y-4">
        {/* Transaction Type */}
        <div>
          <Label className="font-medium text-slate-700">Transaction Type <span className="text-red-500">*</span></Label>
          <RadioGroup
            value={transactionType}
            onValueChange={(value: string) => setTransactionType(value)}
            className="mt-2 grid grid-cols-2 gap-x-4 gap-y-2"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value={TransactionType.DIVIDEND} id="DIVIDEND" />
              <Label htmlFor="DIVIDEND" className="font-normal text-slate-700 cursor-pointer">
                Dividend
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value={TransactionType.BROKERAGE_INTEREST} id="BROKERAGE_INTEREST" />
              <Label htmlFor="BROKERAGE_INTEREST" className="font-normal text-slate-700 cursor-pointer">
                Brokerage Interest
              </Label>
            </div>
          </RadioGroup>
        </div>

        {/* Transaction Date */}
        <div>
          <Label htmlFor="transactionDate" className="font-medium text-slate-700">Transaction Date <span className="text-red-500">*</span></Label>
          <Input 
            id="transactionDate" 
            type="date" 
            value={transactionDate} 
            onChange={(e) => setTransactionDate(e.target.value)} 
            required 
            className="mt-1" 
          />
        </div>

        {/* Fund Selection */}
        <div>
          <Label htmlFor="fundId" className="font-medium text-slate-700">Fund <span className="text-red-500">*</span></Label>
          <Select value={fundId} onValueChange={setFundId} required>
            <SelectTrigger id="fundId" className="mt-1 w-full">
              <SelectValue placeholder="Select a fund..." />
            </SelectTrigger>
            <SelectContent>
              {funds.map(fund => (
                <SelectItem key={fund.id} value={fund.id}>{fund.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Asset Selection - Only for Dividend */}
        {transactionType === TransactionType.DIVIDEND && (
          <div>
            <Label htmlFor="assetId" className="font-medium text-slate-700">Stock/ETF <span className="text-red-500">*</span></Label>
            <Select value={assetId} onValueChange={setAssetId} required>
              <SelectTrigger id="assetId" className="mt-1 w-full">
                <SelectValue placeholder="Select a stock..." />
              </SelectTrigger>
              <SelectContent>
                {stockAssets.map(asset => (
                  <SelectItem key={asset.id} value={asset.id}>{asset.symbol} - {asset.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {/* Amount */}
        <div>
          <Label htmlFor="totalAmount" className="font-medium text-slate-700">Total Amount <span className="text-red-500">*</span></Label>
          <Input 
            id="totalAmount" 
            type="number" 
            value={totalAmount} 
            onChange={(e) => setTotalAmount(e.target.value)} 
            placeholder="0.00" 
            step="0.01" 
            min="0.01" 
            required 
            className="mt-1" 
          />
          <p className="text-xs text-slate-500 mt-0.5">
            {transactionType === TransactionType.DIVIDEND ? 'Gross dividend amount received' : 'Interest earned on brokerage cash'}
          </p>
        </div>

        {/* Fees/Commissions */}
        <div>
          <Label htmlFor="feesCommissions" className="font-medium text-slate-700">Fees/Commissions</Label>
          <Input 
            id="feesCommissions" 
            type="number" 
            value={feesCommissions} 
            onChange={(e) => setFeesCommissions(e.target.value)} 
            placeholder="0.00" 
            step="0.01" 
            min="0" 
            className="mt-1" 
          />
        </div>

        {/* Description */}
        <div>
          <Label htmlFor="description" className="font-medium text-slate-700">Description/Notes</Label>
          <Textarea 
            id="description" 
            value={description} 
            onChange={(e) => setDescription(e.target.value)} 
            placeholder="Optional notes..." 
            rows={2} 
            className="mt-1" 
          />
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200 mt-6">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
        )}
        <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={isSubmitting || funds.length === 0}>
          {isSubmitting ? 'Saving...' : 'Save Transaction'}
        </Button>
      </div>
    </form>
  );
};

export default LogDividendInterestForm;