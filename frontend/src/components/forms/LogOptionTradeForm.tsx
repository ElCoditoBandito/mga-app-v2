
// frontend/src/components/forms/LogOptionTradeForm.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { CardHeader, CardTitle, CardDescription } from '@/components/ui/card'; // For consistent header styling
import { AlertCircle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';
import { OptionTransactionType, OptionType } from '@/enums';

// --- Mock Data Structures (align with backend Pydantic schemas) ---
interface FundSlim {
  id: string;
  name: string;
}

export interface OptionTradeFormData {
  fund_id: string;                        // required
  transaction_type: OptionTransactionType; // required
  underlying_symbol: string;              // required (for AssetCreateOption)
  option_type: OptionType;                // required (for AssetCreateOption)
  strike_price: number;                   // required (for AssetCreateOption)
  expiration_date: string;                // required, ISO format (for AssetCreateOption)
  option_symbol_name?: string;             // optional (for AssetCreateOption.name, can be auto-generated)
  transaction_date: string;               // required, ISO format
  quantity_contracts: number;             // required, positive (number of contracts)
  premium_per_contract: number;         // required, positive
  fees_commissions?: number;              // optional, defaults to 0
  description?: string;                   // optional
}

interface LogOptionTradeFormProps {
  funds: FundSlim[];
  initialFundId?: string;
  onSubmit: (data: OptionTradeFormData) => Promise<void>;
  onCancel?: () => void;
  // Consider passing existing underlying assets for validation/lookup
}

const LogOptionTradeForm: React.FC<LogOptionTradeFormProps> = ({
  funds,
  initialFundId,
  onSubmit,
  onCancel,
}) => {
  const [fundId, setFundId] = useState<string>(initialFundId || (funds.length > 0 ? funds[0].id : ''));
  const [transactionType, setTransactionType] = useState<OptionTransactionType>(OptionTransactionType.BUY_TO_OPEN);
  const [underlyingSymbol, setUnderlyingSymbol] = useState('');
  const [optionType, setOptionType] = useState<OptionType>(OptionType.CALL);
  const [strikePrice, setStrikePrice] = useState<string>('');
  const [expirationDate, setExpirationDate] = useState<string>('');
  const [optionSymbolName, setOptionSymbolName] = useState('');
  const [transactionDate, setTransactionDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [quantityContracts, setQuantityContracts] = useState<string>('');
  const [premiumPerContract, setPremiumPerContract] = useState<string>('');
  const [feesCommissions, setFeesCommissions] = useState<string>('0');
  const [description, setDescription] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calculatedTotal = useMemo(() => {
    const numContracts = parseFloat(quantityContracts);
    const numPremium = parseFloat(premiumPerContract);
    const numFees = parseFloat(feesCommissions) || 0;

    if (isNaN(numContracts) || isNaN(numPremium) || numContracts <= 0 || numPremium <= 0) {
      return null;
    }
    // Option value is typically per share, so multiply by 100 shares per contract
    const baseAmount = numContracts * numPremium * 100;
    
    // For BUY_TO_OPEN and BUY_TO_CLOSE, it's a debit (cost)
    // For SELL_TO_OPEN and SELL_TO_CLOSE, it's a credit (proceeds)
    if (transactionType === OptionTransactionType.BUY_TO_OPEN || transactionType === OptionTransactionType.BUY_TO_CLOSE) {
      return baseAmount + numFees; // Cost, so add fees
    } else { // SELL_TO_OPEN or SELL_TO_CLOSE
      return baseAmount - numFees; // Proceeds, so subtract fees
    }
  }, [quantityContracts, premiumPerContract, feesCommissions, transactionType]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const numStrike = parseFloat(strikePrice);
    const numContracts = parseFloat(quantityContracts);
    const numPremium = parseFloat(premiumPerContract);
    const numFees = parseFloat(feesCommissions) || 0;

    if (!fundId) { setError('Fund assignment is required.'); return; }
    if (!underlyingSymbol.trim()) { setError('Underlying Ticker Symbol is required.'); return; }
    if (isNaN(numStrike) || numStrike <= 0) { setError('Valid Strike Price is required.'); return; }
    if (!expirationDate) { setError('Expiration Date is required.'); return; }
    if (isNaN(numContracts) || numContracts <= 0) { setError('Valid number of contracts is required.'); return; }
    if (isNaN(numPremium) || numPremium <= 0) { setError('Valid premium per contract is required.'); return; }
    if (isNaN(numFees) || numFees < 0) { setError('Fees/Commissions cannot be negative.'); return; }

    const formData: OptionTradeFormData = {
      fund_id: fundId,
      transaction_type: transactionType,
      underlying_symbol: underlyingSymbol.toUpperCase().trim(),
      option_type: optionType,
      strike_price: numStrike,
      expiration_date: expirationDate,
      option_symbol_name: optionSymbolName.trim() || undefined, // Backend can auto-generate if empty
      transaction_date: transactionDate,
      quantity_contracts: numContracts,
      premium_per_contract: numPremium,
      fees_commissions: numFees,
      description: description.trim() || undefined,
    };

    setIsSubmitting(true);
    try {
      await onSubmit(formData);
    } catch (submissionError: unknown) {
      setError(submissionError instanceof Error ? submissionError.message : 'Failed to save option trade. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  useEffect(() => {
    if (initialFundId && funds.find(f => f.id === initialFundId)) {
        setFundId(initialFundId);
    } else if (funds.length > 0 && !initialFundId) {
        setFundId(funds[0].id);
    }
  }, [initialFundId, funds]);

  // Auto-generate option symbol suggestion
  const suggestedOptionSymbol = useMemo(() => {
    if (!underlyingSymbol || !expirationDate || !strikePrice || !optionType) return '';
    const date = new Date(expirationDate + 'T00:00:00'); // Ensure parsing as local date
    const year = date.getFullYear().toString().slice(-2);
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const strike = parseFloat(strikePrice).toFixed(0).padStart(5, '0'); // Example padding for OCC format
    return `${underlyingSymbol.toUpperCase()}${year}${month}${day}${optionType.charAt(0)}${strike}`;
  }, [underlyingSymbol, expirationDate, strikePrice, optionType]);

  useEffect(() => {
    if (!optionSymbolName && suggestedOptionSymbol) {
        // setOptionSymbolName(suggestedOptionSymbol); // Uncomment to auto-fill
    }
  }, [suggestedOptionSymbol, optionSymbolName]);


  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <CardHeader className="px-0 pt-0">
        <CardTitle className="text-xl font-semibold text-slate-800">Log Option Trade</CardTitle>
        <CardDescription className="text-sm text-slate-600">
          Manually enter an option purchase or sale for a specific fund.
        </CardDescription>
      </CardHeader>

      {error && (
        <div className="p-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700 flex items-start">
          <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
          <div><span className="font-medium">Error:</span> {error}</div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
        {/* Fund Assignment */}
        <div className="md:col-span-2">
          <Label htmlFor="fundIdOpt" className="font-medium text-slate-700">Assign to Fund <span className="text-red-500">*</span></Label>
          <Select value={fundId} onValueChange={setFundId} required>
            <SelectTrigger id="fundIdOpt" className="mt-1 w-full"><SelectValue placeholder="Select a fund..." /></SelectTrigger>
            <SelectContent>{funds.map(fund => <SelectItem key={fund.id} value={fund.id}>{fund.name}</SelectItem>)}</SelectContent>
          </Select>
        </div>

        {/* Transaction Type */}
        <div className="md:col-span-2">
          <Label className="font-medium text-slate-700">Trade Type <span className="text-red-500">*</span></Label>
          <RadioGroup
            value={transactionType}
            onValueChange={(value: OptionTransactionType) => setTransactionType(value)}
            className="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-2"
          >
            {Object.entries(OptionTransactionType).map(([key, value]) => (
                <div key={value} className="flex items-center space-x-2">
                    <RadioGroupItem value={value} id={value} />
                    <Label htmlFor={value} className="font-normal text-slate-700 cursor-pointer text-sm">
                        {key.replace(/_/g, ' ').replace('OPTION', '(Opt)')} {/* Simple formatting */}
                    </Label>
                </div>
            ))}
          </RadioGroup>
        </div>

        {/* Option Asset Details - Grouped */}
        <div className="md:col-span-2 space-y-4 border-t border-slate-200 pt-4 mt-2">
            <h3 className="text-md font-semibold text-slate-700">Option Contract Details</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-4">
                <div><Label htmlFor="underlyingSymbol">Underlying Ticker <span className="text-red-500">*</span></Label><Input id="underlyingSymbol" value={underlyingSymbol} onChange={(e) => setUnderlyingSymbol(e.target.value.toUpperCase())} placeholder="e.g., AAPL" required className="mt-1" /></div>
                <div><Label htmlFor="optionType">Option Type <span className="text-red-500">*</span></Label><Select value={optionType} onValueChange={(v: string) => setOptionType(v as OptionType)} required><SelectTrigger id="optionType" className="mt-1 w-full"><SelectValue /></SelectTrigger><SelectContent>{Object.values(OptionType).map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent></Select></div>
                <div><Label htmlFor="strikePrice">Strike Price <span className="text-red-500">*</span></Label><Input id="strikePrice" type="number" value={strikePrice} onChange={(e) => setStrikePrice(e.target.value)} placeholder="0.00" step="any" min="0.01" required className="mt-1" /></div>
                <div><Label htmlFor="expirationDate">Expiration Date <span className="text-red-500">*</span></Label><Input id="expirationDate" type="date" value={expirationDate} onChange={(e) => setExpirationDate(e.target.value)} required className="mt-1" /></div>
            </div>
            <div>
                <Label htmlFor="optionSymbolName">Option Symbol / Name</Label>
                <Input id="optionSymbolName" value={optionSymbolName} onChange={(e) => setOptionSymbolName(e.target.value)} placeholder={suggestedOptionSymbol || "e.g., AAPL251219C00180000"} className="mt-1" />
                <p className="text-xs text-slate-500 mt-1 flex items-start"><Info className="h-3 w-3 mr-1 mt-0.5 flex-shrink-0" />If blank, system may attempt to generate. Ensure underlying ticker exists or can be created.</p>
            </div>
        </div>

        {/* Trade Details - Grouped */}
        <div className="md:col-span-2 space-y-4 border-t border-slate-200 pt-4 mt-2">
            <h3 className="text-md font-semibold text-slate-700">Trade Execution Details</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-4">
                <div><Label htmlFor="transactionDateOpt">Transaction Date <span className="text-red-500">*</span></Label><Input id="transactionDateOpt" type="date" value={transactionDate} onChange={(e) => setTransactionDate(e.target.value)} required className="mt-1" /></div>
                <div><Label htmlFor="quantityContracts">No. of Contracts <span className="text-red-500">*</span></Label><Input id="quantityContracts" type="number" value={quantityContracts} onChange={(e) => setQuantityContracts(e.target.value)} placeholder="0" step="1" min="1" required className="mt-1" /></div>
                <div><Label htmlFor="premiumPerContract">Premium <span className="text-red-500">*</span></Label><Input id="premiumPerContract" type="number" value={premiumPerContract} onChange={(e) => setPremiumPerContract(e.target.value)} placeholder="0.00" step="any" min="0.01" required className="mt-1" /><p className="text-xs text-slate-500 mt-0.5">(Price per share)</p></div>
                <div className="md:col-span-1"><Label htmlFor="feesCommissionsOpt">Fees/Commissions</Label><Input id="feesCommissionsOpt" type="number" value={feesCommissions} onChange={(e) => setFeesCommissions(e.target.value)} placeholder="0.00" step="any" min="0" className="mt-1" /></div>
                <div className="md:col-span-2 flex flex-col justify-end">
                    <Label className="font-medium text-slate-700">Total {transactionType.startsWith('BUY') ? 'Cost' : 'Proceeds'}</Label>
                    <div className={cn("mt-1 p-2 rounded-md text-lg font-semibold h-[38px] flex items-center", calculatedTotal === null ? "bg-slate-100 text-slate-500 italic" : (transactionType.startsWith('BUY') ? "bg-red-50 border-red-200 text-red-700" : "bg-green-50 border-green-200 text-green-700"))}>
                        {calculatedTotal !== null ? `$${Math.abs(calculatedTotal).toFixed(2)}` : 'Enter contracts & premium'}
                    </div>
                </div>
            </div>
        </div>

        {/* Notes */}
        <div className="md:col-span-2 border-t border-slate-200 pt-4 mt-2">
          <Label htmlFor="descriptionOpt">Description/Notes</Label>
          <Textarea id="descriptionOpt" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Optional notes about the option trade..." rows={2} className="mt-1" />
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-slate-200 mt-6">
        {onCancel && (<Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>Cancel</Button>)}
        <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={isSubmitting || !fundId || funds.length === 0}>
          {isSubmitting ? 'Saving Option Trade...' : 'Save Option Trade'}
        </Button>
      </div>
    </form>
  );
};

export default LogOptionTradeForm;
