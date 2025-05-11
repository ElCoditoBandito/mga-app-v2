
// frontend/src/components/forms/RecordMemberTransactionForm.tsx
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { CardHeader, CardTitle, CardDescription } from '@/components/ui/card'; // For consistent header styling
import { AlertCircle, Info } from 'lucide-react';
import { MemberTransactionType } from '@/enums';

// --- Mock Data Structures (align with backend Pydantic schemas) ---
interface UserSlim {
  id: string; // user.id
  name: string; // display name (e.g., user.email or user.name)
}

// Based on MemberTransactionCreate
export interface MemberTransactionFormData {
  user_id: string; // Selected user's ID
  club_id: string; // Current club context, passed or known by parent
  transaction_type: MemberTransactionType;
  transaction_date: string; // ISO format
  amount: number; // Positive decimal
  notes?: string;
  // Backend will calculate units_transacted and unit_value_used
}

interface RecordMemberTransactionFormProps {
  clubId: string; // To be passed to the backend
  members: UserSlim[]; // List of active club members
  latestUnitValue?: number | null;
  latestValuationDate?: string | null;
  onSubmit: (data: MemberTransactionFormData) => Promise<void>;
  onCancel?: () => void;
}

const RecordMemberTransactionForm: React.FC<RecordMemberTransactionFormProps> = ({
  clubId,
  members,
  latestUnitValue,
  latestValuationDate,
  onSubmit,
  onCancel,
}) => {
  const [userId, setUserId] = useState<string>(members.length > 0 ? members[0].id : '');
  const [transactionType, setTransactionType] = useState<MemberTransactionType>(MemberTransactionType.DEPOSIT);
  const [transactionDate, setTransactionDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [amount, setAmount] = useState<string>('');
  const [notes, setNotes] = useState<string>('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const numAmount = parseFloat(amount);

    if (!userId) { setError('Member selection is required.'); return; }
    if (isNaN(numAmount) || numAmount <= 0) { setError('Valid positive amount is required.'); return; }
    if (!transactionDate) { setError('Transaction date is required.'); return; }

    const formData: MemberTransactionFormData = {
      user_id: userId,
      club_id: clubId,
      transaction_type: transactionType,
      transaction_date: transactionDate,
      amount: numAmount,
      notes: notes.trim() || undefined,
    };

    setIsSubmitting(true);
    try {
      await onSubmit(formData);
      // Optionally reset form here
      setUserId(members.length > 0 ? members[0].id : '');
      setTransactionType(MemberTransactionType.DEPOSIT);
      setTransactionDate(new Date().toISOString().split('T')[0]);
      setAmount('');
      setNotes('');
    } catch (submissionError: unknown) {
      setError(submissionError instanceof Error ? submissionError.message : 'Failed to record transaction. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  useEffect(() => {
    if (members.length > 0 && !userId) {
        setUserId(members[0].id);
    }
  }, [members, userId]);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <CardHeader className="px-0 pt-0">
        <CardTitle className="text-xl font-semibold text-slate-800">Record Member Financial Transaction</CardTitle>
        <CardDescription className="text-sm text-slate-600">
          Log a member's cash deposit into or withdrawal from the club bank account.
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
          <Label htmlFor="memberId" className="font-medium text-slate-700">Member <span className="text-red-500">*</span></Label>
          <Select value={userId} onValueChange={setUserId} required>
            <SelectTrigger id="memberId" className="mt-1 w-full">
              <SelectValue placeholder="Select a member..." />
            </SelectTrigger>
            <SelectContent>
              {members.length > 0 ? (
                members.map(member => <SelectItem key={member.id} value={member.id}>{member.name}</SelectItem>)
              ) : (
                <SelectItem value="" disabled>No members available</SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label className="font-medium text-slate-700">Transaction Type <span className="text-red-500">*</span></Label>
          <RadioGroup
            value={transactionType}
            onValueChange={(value: MemberTransactionType) => setTransactionType(value)}
            className="mt-2 flex space-x-4"
          >
            <div className="flex items-center space-x-2">
              <RadioGroupItem value={MemberTransactionType.DEPOSIT} id="deposit" />
              <Label htmlFor="deposit" className="font-normal text-slate-700 cursor-pointer">Deposit</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value={MemberTransactionType.WITHDRAWAL} id="withdrawal" />
              <Label htmlFor="withdrawal" className="font-normal text-slate-700 cursor-pointer">Withdrawal</Label>
            </div>
          </RadioGroup>
        </div>

        <div>
          <Label htmlFor="memTxDate" className="font-medium text-slate-700">Transaction Date <span className="text-red-500">*</span></Label>
          <Input id="memTxDate" type="date" value={transactionDate} onChange={(e) => setTransactionDate(e.target.value)} required className="mt-1" />
        </div>

        <div>
          <Label htmlFor="memTxAmount" className="font-medium text-slate-700">Amount <span className="text-red-500">*</span></Label>
          <Input id="memTxAmount" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="0.00" step="0.01" min="0.01" required className="mt-1" />
        </div>

        <div>
          <Label htmlFor="memTxNotes" className="font-medium text-slate-700">Notes</Label>
          <Textarea id="memTxNotes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional notes for this transaction..." rows={2} className="mt-1" />
        </div>

        {/* Informational Display */}
        {(latestUnitValue !== undefined && latestUnitValue !== null && latestValuationDate) && (
          <div className="p-3 rounded-md bg-blue-50 border border-blue-200 text-sm text-blue-700 flex items-start">
            <Info className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
            <div>
                The latest unit value of <span className="font-semibold">${latestUnitValue.toFixed(4)}</span> (as of {new Date(latestValuationDate).toLocaleDateString()}) 
                will be used by the system to calculate units for this transaction. 
                Remember to run EOD valuation if significant market changes occurred today before this transaction.
            </div>
          </div>
        )}
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200 mt-6">
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
            Cancel
          </Button>
        )}
        <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={isSubmitting || members.length === 0}>
          {isSubmitting ? 'Saving Transaction...' : 'Save Transaction'}
        </Button>
      </div>
    </form>
  );
};

export default RecordMemberTransactionForm;
