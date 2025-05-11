
// frontend/src/pages/FundsPage.tsx
import React, { useState, useMemo, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch'; // Assuming npx shadcn-ui@latest add switch
import { Label } from '@/components/ui/label';   // Assuming npx shadcn-ui@latest add label
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger, DialogClose } from '@/components/ui/dialog';
// import { Skeleton } from '@/components/ui/skeleton';
import { PlusCircle, Edit3, Settings2, AlertTriangle, Save } from 'lucide-react';
import { cn } from '@/lib/utils';

// Mock Data - Replace with API calls
interface Fund {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  brokerage_cash_balance: number;
}

interface FundSplit {
  fund_id: string;
  fund_name: string; 
  split_percentage: number; 
}

interface FundsPageData {
  clubId: string;
  clubName: string;
  funds: Fund[];
  fundSplits: FundSplit[];
  isAdmin: boolean;
}

const MOCK_FUNDS_PAGE_DATA_STORE: { current: FundsPageData } = {
    current: {
        clubId: 'club123',
        clubName: 'Eagle Investors Club',
        isAdmin: true,
        funds: [
            { id: 'fundA', name: 'US Equities Fund', description: 'Focus on S&P 500 Index ETFs and large-cap stocks.', is_active: true, brokerage_cash_balance: 5000.25 },
            { id: 'fundB', name: 'Global Growth Fund', description: 'Diversified international equities with high growth potential.', is_active: true, brokerage_cash_balance: 10000.50 },
            { id: 'fundC', name: 'Fixed Income Fund', description: 'Bonds and other fixed income securities for stability.', is_active: false, brokerage_cash_balance: 2500.00 },
        ],
        fundSplits: [
            { fund_id: 'fundA', fund_name: 'US Equities Fund', split_percentage: 0.6 },
            { fund_id: 'fundB', fund_name: 'Global Growth Fund', split_percentage: 0.4 },
        ],
    }
};

const formatCurrency = (value?: number | null) => {
  if (value == null) return 'N/A';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
};

// --- Create/Edit Fund Dialog Form ---
interface FundFormData {
    name: string;
    description: string;
    is_active: boolean;
}

interface FundDialogFormProps {
  initialData?: FundFormData;
  onSave: (data: FundFormData) => void;
  dialogCloseRef?: React.Ref<HTMLButtonElement>; // Make optional if not always used
  mode: 'create' | 'edit';
}

const FundDialogForm: React.FC<FundDialogFormProps> = ({ initialData, onSave, dialogCloseRef, mode }) => {
  const [name, setName] = useState(initialData?.name || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [isActive, setIsActive] = useState(initialData?.is_active === undefined ? true : initialData.is_active);

  useEffect(() => {
    if (initialData) {
        setName(initialData.name || '');
        setDescription(initialData.description || '');
        setIsActive(initialData.is_active === undefined ? true : initialData.is_active);
    }
  }, [initialData]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({ name, description, is_active: isActive });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 pt-2">
      <div>
        <Label htmlFor="fundName" className="font-medium text-slate-700">Fund Name</Label>
        <Input
          id="fundName"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="E.g., Technology Growth Fund"
          required
          className="mt-1 border-slate-300 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>
      <div>
        <Label htmlFor="fundDescription" className="font-medium text-slate-700">Fund Description/Investment Style</Label>
        <Textarea
          id="fundDescription"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe the fund's investment strategy, goals, etc."
          rows={3}
          className="mt-1 border-slate-300 focus:border-blue-500 focus:ring-blue-500"
        />
      </div>
      {mode === 'edit' && (
        <div className="flex items-center space-x-2 pt-2">
          <Switch
            id="is_active"
            checked={isActive}
            onCheckedChange={setIsActive}
            aria-labelledby="is_active_label"
          />
          <Label htmlFor="is_active" id="is_active_label" className="text-slate-700 cursor-pointer">
            Fund is Active
          </Label>
        </div>
      )}
      <DialogFooter className="mt-8">
        <DialogClose asChild>
          <Button type="button" variant="outline" ref={dialogCloseRef}>Cancel</Button>
        </DialogClose>
        <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
          <Save className="mr-2 h-4 w-4" /> {mode === 'create' ? 'Create Fund' : 'Save Changes'}
        </Button>
      </DialogFooter>
    </form>
  );
};

const FundsPage = () => {
  const { clubId } = useParams<{ clubId: string }>();
  const [pageData, setPageData] = useState<FundsPageData>(MOCK_FUNDS_PAGE_DATA_STORE.current);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [isLoading, _setIsLoading] = useState(false); // Mock loading state
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [error, _setError] = useState<Error | null>(null); // Mock error state

  const [fundSplits, setFundSplits] = useState<FundSplit[]>(pageData.fundSplits);
  const [showCreateFundDialog, setShowCreateFundDialog] = useState(false);
  const [editingFund, setEditingFund] = useState<Fund | null>(null);
  const [showEditFundDialog, setShowEditFundDialog] = useState(false);

  const createFundDialogCloseRef = React.useRef<HTMLButtonElement>(null);
  const editFundDialogCloseRef = React.useRef<HTMLButtonElement>(null);
  
  useEffect(() => {
    // Simulate fetching data or if pageData changes from props/context in real app
    setFundSplits(pageData.fundSplits);
  }, [pageData.fundSplits]);

  const handleCreateFund = (fundData: FundFormData) => {
    console.log('Creating new fund:', fundData);
    const newFund: Fund = {
        ...fundData,
        id: `fund${Math.random().toString(36).substr(2, 9)}`,
        brokerage_cash_balance: 0,
    };
    const updatedFunds = [...pageData.funds, newFund];
    const updatedSplits = [...fundSplits];
    if (newFund.is_active) {
        updatedSplits.push({ fund_id: newFund.id, fund_name: newFund.name, split_percentage: 0 });
    }
    setPageData(prev => ({ ...prev, funds: updatedFunds }));
    setFundSplits(updatedSplits);
    setShowCreateFundDialog(false);
  };

  const handleEditFundTrigger = (fund: Fund) => {
    setEditingFund(fund);
    setShowEditFundDialog(true);
  };

  const handleSaveEditedFund = (updatedData: FundFormData) => {
    if (!editingFund) return;
    console.log('Saving fund:', editingFund.id, updatedData);
    const updatedFunds = pageData.funds.map(f => f.id === editingFund.id ? { ...editingFund, ...updatedData } : f);
    
    let updatedSplits = fundSplits.map(s => s.fund_id === editingFund.id ? {...s, fund_name: updatedData.name} : s);

    // If fund is made inactive, remove it from splits or set its percentage to 0 and potentially adjust others.
    // If fund is made active, add it to splits if not present, potentially with 0%.
    const wasActive = editingFund.is_active;
    const nowActive = updatedData.is_active;

    if (wasActive && !nowActive) { // Became inactive
        // Option 1: Remove from splits. User must re-add if reactivated.
        updatedSplits = updatedSplits.filter(s => s.fund_id !== editingFund.id);
        // Option 2: Keep in splits but its percentage doesn't count to 100% total (handled by totalAllocatedPercentage logic)
    } else if (!wasActive && nowActive) { // Became active
        if (!updatedSplits.find(s => s.fund_id === editingFund.id)) {
            updatedSplits.push({ fund_id: editingFund.id, fund_name: updatedData.name, split_percentage: 0 });
        }
    }

    setPageData(prev => ({ ...prev, funds: updatedFunds }));
    setFundSplits(updatedSplits);
    setShowEditFundDialog(false);
    setEditingFund(null);
  };

  const handleSplitChange = (fundId: string, newPercentageStr: string) => {
    let newPercentage = parseFloat(newPercentageStr);
    if (isNaN(newPercentage)) newPercentage = 0;
    newPercentage = Math.max(0, Math.min(100, newPercentage)); // Clamp between 0 and 100

    setFundSplits(
      fundSplits.map((split) =>
        split.fund_id === fundId ? { ...split, split_percentage: newPercentage / 100 } : split
      )
    );
  };

  const totalAllocatedPercentage = useMemo(() => {
    return fundSplits.reduce((sum, split) => {
        const fundDetails = pageData.funds.find(f => f.id === split.fund_id);
        return fundDetails?.is_active ? sum + (split.split_percentage * 100) : sum;
    }, 0);
  }, [fundSplits, pageData.funds]);

  if (isLoading) { /* Skeleton */ }
  if (error || !pageData) { /* Error */ }

  const { funds, isAdmin } = pageData;
  const activeFundsForSplitTable = funds.filter(f => f.is_active);

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Club Funds</h1>
          <p className="text-slate-600">Manage your club's investment funds and cash allocation strategies.</p>
        </div>
        {isAdmin && (
          <Dialog open={showCreateFundDialog} onOpenChange={setShowCreateFundDialog}>
            <DialogTrigger asChild>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <PlusCircle className="mr-2 h-5 w-5" /> Create New Fund
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg bg-white">
              <DialogHeader>
                <DialogTitle className="text-slate-800">Create New Fund</DialogTitle>
                <DialogDescription>Define a new investment fund for your club. New funds are active by default.</DialogDescription>
              </DialogHeader>
              <FundDialogForm mode="create" onSave={handleCreateFund} dialogCloseRef={createFundDialogCloseRef} initialData={{ name: '', description: '', is_active: true }} />
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Fund List/Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 md:gap-6">
        {funds.map((fund) => (
          <Card key={fund.id} className="bg-white border-slate-200/75 shadow-sm hover:shadow-md transition-all flex flex-col">
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-lg font-medium text-slate-800">{fund.name}</CardTitle>
                <span className={cn("px-2 py-0.5 rounded-full text-xs font-semibold", fund.is_active ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-600")}>
                  {fund.is_active ? "Active" : "Inactive"}
                </span>
              </div>
              <CardDescription className="text-sm text-slate-600 line-clamp-2 pt-1 h-[40px]">{fund.description}</CardDescription>
            </CardHeader>
            <CardContent className="flex-grow space-y-2">
              <div className="text-sm text-slate-500">Brokerage Cash: <span className="font-medium text-slate-700">{formatCurrency(fund.brokerage_cash_balance)}</span></div>
            </CardContent>
            <CardFooter className="border-t border-slate-200/75 pt-4 flex gap-2">
              <Button asChild variant="outline" className="flex-1 bg-white hover:bg-slate-50">
                <Link to={`/club/${clubId}/funds/${fund.id}`}>View Details</Link>
              </Button>
              {isAdmin && (
                <Button variant="ghost" size="icon" className="text-slate-500 hover:text-blue-600 hover:bg-slate-100" onClick={() => handleEditFundTrigger(fund)}>
                  <Edit3 className="h-5 w-5" /><span className="sr-only">Edit Fund</span>
                </Button>
              )}
            </CardFooter>
          </Card>
        ))}
        {funds.length === 0 && null /* TODO: Implement UI for when there are no funds */}
      </div>

      {/* Edit Fund Dialog */}
      {editingFund && (
        <Dialog open={showEditFundDialog} onOpenChange={(isOpen) => { setShowEditFundDialog(isOpen); if (!isOpen) setEditingFund(null); }}>
            <DialogContent className="sm:max-w-lg bg-white">
                <DialogHeader>
                    <DialogTitle className="text-slate-800">Edit Fund: {editingFund.name}</DialogTitle>
                    <DialogDescription>Update the details for this investment fund.</DialogDescription>
                </DialogHeader>
                <FundDialogForm
                    mode="edit"
                    initialData={editingFund} // Pass full fund object
                    onSave={handleSaveEditedFund}
                    dialogCloseRef={editFundDialogCloseRef}
                />
            </DialogContent>
        </Dialog>
      )}

      {/* New Cash Allocation Splits */}
      {isAdmin && activeFundsForSplitTable.length > 0 && (
        <Card className="bg-white border-slate-200/75 shadow-sm hover:shadow-md transition-all">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-slate-800 flex items-center"><Settings2 className="mr-2 h-5 w-5 text-blue-600" /> New Bank Transfer Allocations</CardTitle>
            <CardDescription className="text-sm text-slate-600">Set the percentage of new cash transfers from the club's bank account that should be allocated to each active fund. Total should be 100%.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader><TableRow className="hover:bg-transparent"><TableHead className="text-slate-700 font-medium w-[60%]">Active Fund Name</TableHead><TableHead className="text-slate-700 font-medium text-right">Allocation Percentage (%)</TableHead></TableRow></TableHeader>
              <TableBody>
                {activeFundsForSplitTable.map((fund) => {
                  const split = fundSplits.find(s => s.fund_id === fund.id);
                  return (
                    <TableRow key={fund.id} className="hover:bg-slate-50/50">
                      <TableCell className="font-medium text-slate-800">{fund.name}</TableCell>
                      <TableCell className="text-right">
                        <Input type="number" value={split ? (split.split_percentage * 100).toString() : '0'} onChange={(e) => handleSplitChange(fund.id, e.target.value)} className="w-24 h-9 text-right border-slate-300 focus:border-blue-500 focus:ring-blue-500 ml-auto" min="0" max="100" step="0.01"/>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
            <div className="mt-4 p-3 rounded-md flex justify-between items-center border border-slate-200 bg-slate-50/80">
                <div>
                    <span className={cn("text-sm font-semibold", totalAllocatedPercentage === 100 ? "text-slate-700" : "text-amber-700")}>Total Allocated: {totalAllocatedPercentage.toFixed(2)}%</span>
                    {totalAllocatedPercentage !== 100 && (
                        <p className="text-xs text-amber-600 flex items-center mt-0.5"><AlertTriangle className="mr-1.5 h-3.5 w-3.5" />Total should be 100% for funds receiving new cash.</p>
                    )}
                </div>
              <Button className="bg-blue-600 hover:bg-blue-700" onClick={() => console.log('Save fund splits:', fundSplits.filter(s => activeFundsForSplitTable.find(f=>f.id === s.fund_id)))} disabled={totalAllocatedPercentage !== 100 && activeFundsForSplitTable.length > 0}>
                <Save className="mr-2 h-4 w-4" /> Save Allocations
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
      {isAdmin && activeFundsForSplitTable.length === 0 && funds.length > 0 && ( // TODO: Implement UI for when there are no active funds for split table, but inactive funds exist
  null )}
    </div>
  );
};

export default FundsPage;
