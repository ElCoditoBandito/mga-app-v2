
// frontend/src/components/forms/LogClubExpenseForm.tsx
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { AlertCircle } from 'lucide-react';

// Based on TransactionCreateClubExpense
export interface ClubExpenseFormData {
  club_id: string; // Current club context
  transaction_date: string; // ISO format, required
  total_amount: number;     // Positive decimal, required (will be stored as negative on backend for expense)
  description: string;      // Required
  fees_commissions?: number; // Optional, defaults to 0 (usually not for simple expenses)
}

interface LogClubExpenseFormProps {
  clubId: string;
  onSubmit: (data: ClubExpenseFormData) => Promise<void>;
  onCancel?: () => void;
}

const LogClubExpenseForm: React.FC<LogClubExpenseFormProps> = ({
  clubId,
  onSubmit,
  onCancel,
}) => {
  const [transactionDate, setTransactionDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [totalAmount, setTotalAmount] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [feesCommissions, setFeesCommissions] = useState<string>('0');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const numTotalAmount = parseFloat(totalAmount);
    const numFees = parseFloat(feesCommissions) || 0;

    if (!transactionDate) { setError('Expense Date is required.'); return; }
    if (isNaN(numTotalAmount) || numTotalAmount <= 0) { setError('Valid positive Expense Amount is required.'); return; }
    if (!description.trim()) { setError('Description is required.'); return; }
    if (isNaN(numFees) || numFees < 0) { setError('Fees cannot be negative.'); return; }

    const formData: ClubExpenseFormData = {
      club_id: clubId,
      transaction_date: transactionDate,
      // Backend typically expects expense amount as positive, and will handle making it a debit
      // Or, if API expects negative for expense, send -numTotalAmount
      total_amount: numTotalAmount, 
      description: description.trim(),
      fees_commissions: numFees,
    };

    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      // Reset form on success
      setTransactionDate(new Date().toISOString().split('T')[0]);
      setTotalAmount('');
      setDescription('');
      setFeesCommissions('0');
    } catch (submissionError: any) {
      setError(submissionError.message || 'Failed to log expense. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <CardHeader className="px-0 pt-0">
        <CardTitle className="text-xl font-semibold text-slate-800">Log Club Expense</CardTitle>
        <CardDescription className="text-sm text-slate-600">
          Record an expense paid from the club bank account.
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
          <Label htmlFor="expenseDate" className="font-medium text-slate-700">Expense Date <span className="text-red-500">*</span></Label>
          <Input id="expenseDate" type="date" value={transactionDate} onChange={(e) => setTransactionDate(e.target.value)} required className="mt-1" />
        </div>

        <div>
          <Label htmlFor="expenseAmount" className="font-medium text-slate-700">Expense Amount <span className="text-red-500">*</span></Label>
          <Input id="expenseAmount" type="number" value={totalAmount} onChange={(e) => setTotalAmount(e.target.value)} placeholder="0.00" step="0.01" min="0.01" required className="mt-1" />
        </div>
        
        <div>
          <Label htmlFor="expenseDescription" className="font-medium text-slate-700">Description <span className="text-red-500">*</span></Label>
          <Textarea id="expenseDescription" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="e.g., Annual Software Subscription, Meeting Catering" rows={3} required className="mt-1" />
        </div>

        <div>
          <Label htmlFor="expenseFees" className="font-medium text-slate-700">Fees (if any)</Label>
          <Input id="expenseFees" type="number" value={feesCommissions} onChange={(e) => setFeesCommissions(e.target.value)} placeholder="0.00" step="0.01" min="0" className="mt-1" />
        </div>
      </div>

      <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200 mt-6">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
        )}
        <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={isSubmitting}>
          {isSubmitting ? 'Saving Expense...' : 'Save Expense'}
        </Button>
      </div>
    </form>
  );
};

export default LogClubExpenseForm;
