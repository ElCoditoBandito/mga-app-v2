
// frontend/src/components/forms/LogCashTransferForm.tsx
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { AlertCircle, Info } from 'lucide-react';
import { CashTransferType } from '@/enums';

// --- Data Structures ---
interface FundSlim {
  id: string;
  name: string;
}

// Based on TransactionCreateCashTransfer
export interface CashTransferFormData {
  club_id: string;
  transaction_type: string; // Changed from CashTransferType to string to match backend expectations
  transaction_date: string; // ISO format
  total_amount: number;     // Positive decimal
  fund_id?: string;         // Source fund for BROKERAGE_TO_BANK or INTERFUND_CASH_TRANSFER (source)
  target_fund_id?: string;  // Target fund for INTERFUND_CASH_TRANSFER
  description?: string;
}

interface LogCashTransferFormProps {
  clubId: string;
  funds: FundSlim[]; // Active funds for selection
  onSubmit: (data: CashTransferFormData) => Promise<void>;
  onCancel?: () => void;
}

const LogCashTransferForm: React.FC<LogCashTransferFormProps> = ({
  clubId,
  funds,
  onSubmit,
  onCancel,
}) => {
  const [transactionType, setTransactionType] = useState<CashTransferType>(CashTransferType.BANK_TO_BROKERAGE);
  const [transactionDate, setTransactionDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [totalAmount, setTotalAmount] = useState<string>('');
  const [sourceFundId, setSourceFundId] = useState<string>('');
  const [targetFundId, setTargetFundId] = useState<string>('');
  const [description, setDescription] = useState<string>('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Reset conditional fields when transfer type changes
    setSourceFundId(funds.length > 0 ? funds[0].id : '');
    setTargetFundId(funds.length > 1 ? funds.filter(f => f.id !== (funds.length > 0 ? funds[0].id : ''))[0]?.id || '' : '');
  }, [transactionType, funds]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const numTotalAmount = parseFloat(totalAmount);

    if (isNaN(numTotalAmount) || numTotalAmount <= 0) { setError('Valid positive Transfer Amount is required.'); return; }
    if (!transactionDate) { setError('Transfer Date is required.'); return; }

    const formData: CashTransferFormData = {
      club_id: clubId,
      transaction_type: transactionType, // No mapping needed now as enum values match backend
      transaction_date: transactionDate,
      total_amount: numTotalAmount,
      description: description.trim() || undefined,
    };

    if (transactionType === CashTransferType.BROKERAGE_TO_BANK || transactionType === CashTransferType.INTERFUND_CASH_TRANSFER) {
      if (!sourceFundId) { setError('Source Fund is required for this transfer type.'); return; }
      formData.fund_id = sourceFundId;
    }

    if (transactionType === CashTransferType.INTERFUND_CASH_TRANSFER) {
      if (!targetFundId) { setError('Target Fund is required for Inter-Fund Transfer.'); return; }
      if (sourceFundId === targetFundId) { setError('Source and Target fund cannot be the same for Inter-Fund Transfer.'); return; }
      formData.target_fund_id = targetFundId;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      // Reset form
      setTransactionType(CashTransferType.BANK_TO_BROKERAGE);
      setTransactionDate(new Date().toISOString().split('T')[0]);
      setTotalAmount('');
      setDescription('');
      // Source/Target fund IDs reset by useEffect on transactionType change
    } catch (submissionError: unknown) {
      setError(submissionError instanceof Error ? submissionError.message : 'Failed to log cash transfer. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const availableTargetFunds = funds.filter(f => f.id !== sourceFundId);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <CardHeader className="px-0 pt-0">
        <CardTitle className="text-xl font-semibold text-slate-800">Log Cash Transfer</CardTitle>
        <CardDescription className="text-sm text-slate-600">
          Record cash transfers between Club Bank and Brokerage (Funds), or between two Funds.
        </CardDescription>
      </CardHeader>

      {error && (
        <div className="p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700 flex items-start">
          <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
          <div><span className="font-medium">Error:</span> {error}</div>
        </div>
      )}

      <div className="space-y-4">
        <div>
          <Label htmlFor="transferType" className="font-medium">Transfer Type <span className="text-red-500">*</span></Label>
          <Select value={transactionType} onValueChange={(v: string) => setTransactionType(v as CashTransferType)} required>
            <SelectTrigger id="transferType" className="mt-1 w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={CashTransferType.BANK_TO_BROKERAGE}>Bank to Brokerage (Funds)</SelectItem>
              <SelectItem value={CashTransferType.BROKERAGE_TO_BANK}>Brokerage (Fund) to Bank</SelectItem>
              <SelectItem value={CashTransferType.INTERFUND_CASH_TRANSFER}>Inter-Fund Transfer (Brokerage)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="transferDate" className="font-medium">Transfer Date <span className="text-red-500">*</span></Label>
          <Input id="transferDate" type="date" value={transactionDate} onChange={(e) => setTransactionDate(e.target.value)} required className="mt-1" />
        </div>

        <div>
          <Label htmlFor="transferAmount" className="font-medium">Transfer Amount <span className="text-red-500">*</span></Label>
          <Input id="transferAmount" type="number" value={totalAmount} onChange={(e) => setTotalAmount(e.target.value)} placeholder="0.00" step="0.01" min="0.01" required className="mt-1" />
        </div>

        {/* Conditional Fields */} 
        {(transactionType === CashTransferType.BROKERAGE_TO_BANK || transactionType === CashTransferType.INTERFUND_CASH_TRANSFER) && (
          <div>
            <Label htmlFor="sourceFundId" className="font-medium">Source Fund <span className="text-red-500">*</span></Label>
            <Select value={sourceFundId} onValueChange={setSourceFundId} required>
              <SelectTrigger id="sourceFundId" className="mt-1 w-full"><SelectValue placeholder="Select source fund..." /></SelectTrigger>
              <SelectContent>{funds.map(fund => <SelectItem key={fund.id} value={fund.id}>{fund.name}</SelectItem>)}</SelectContent>
            </Select>
          </div>
        )}

        {transactionType === CashTransferType.INTERFUND_CASH_TRANSFER && (
          <div>
            <Label htmlFor="targetFundId" className="font-medium">Target Fund <span className="text-red-500">*</span></Label>
            <Select value={targetFundId} onValueChange={setTargetFundId} required>
              <SelectTrigger id="targetFundId" className="mt-1 w-full"><SelectValue placeholder="Select target fund..." /></SelectTrigger>
              <SelectContent>
                {availableTargetFunds.length > 0 ? 
                    availableTargetFunds.map(fund => <SelectItem key={fund.id} value={fund.id}>{fund.name}</SelectItem>) :
                    <SelectItem value="" disabled>No other funds available</SelectItem>
                }
                </SelectContent>
            </Select>
             {sourceFundId && targetFundId === sourceFundId && <p className='text-xs text-red-500 mt-1'>Target fund cannot be the same as source fund.</p>}
          </div>
        )}

        {transactionType === CashTransferType.BANK_TO_BROKERAGE && (
             <div className="p-3 rounded-md bg-blue-50 border border-blue-200 text-sm text-blue-700 flex items-start">
                <Info className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                <div>The entered amount will be allocated to active funds based on their defined 'New Cash Allocation' percentages.</div>
            </div>
        )}

        <div>
          <Label htmlFor="transferDescription" className="font-medium">Description/Notes</Label>
          <Textarea id="transferDescription" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional notes..." rows={2} className="mt-1" />
        </div>
      </div>

      <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200 mt-6">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>Cancel</Button>
        )}
        <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={isSubmitting || funds.length === 0}>
          {isSubmitting ? 'Saving Transfer...' : 'Save Transfer'}
        </Button>
      </div>
    </form>
  );
};

export default LogCashTransferForm;
