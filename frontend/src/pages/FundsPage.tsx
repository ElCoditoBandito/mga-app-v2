
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
import { PlusCircle, Edit3, Settings2, AlertTriangle, Save, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ClubRole } from '@/enums';
import { useAuth0 } from '@auth0/auth0-react';
import { toast } from 'sonner';

// Import API hooks
import {
  useClubFunds,
  useFundSplits,
  useUpdateFund,
  useSetFundSplits,
  useClubMembers,
  useCreateClubFund
} from '@/hooks/useApi';
import { ApiError } from '@/lib/apiClient';

// Type definitions
// Extend the API Fund type to include our UI needs
interface Fund {
  id: string;
  club_id: string;
  name: string;
  description?: string; // Make optional to match API type
  is_active: boolean;
  created_at: string;
  updated_at: string;
  brokerage_cash_balance: number; // Required property from API
}

// API FundSplit interface - used for API calls
type ApiFundSplit = {
  fund_id: string;
  split_percentage: number; // Backend expects split_percentage, not percentage
};

// Extended FundSplit for UI
interface ExtendedFundSplit {
  fund_id: string;
  fund_name: string;
  split_percentage: number; // For UI consistency
}

const formatCurrency = (value?: number | null) => {
  if (value == null) return 'N/A';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
};

// --- Create/Edit Fund Dialog Form ---
interface FundFormData {
    name: string;
    description: string; // Keep as required for the form
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
  const { user } = useAuth0();

  // Fetch data using React Query hooks
  const {
    data: apiFunds = [],
    isLoading: isLoadingFunds,
    error: fundsError
  } = useClubFunds(clubId || '');
  
  // Use funds data directly from the API
  const funds = useMemo(() => {
    // The Fund interface now has brokerage_cash_balance as a required property
    // so we can use apiFunds directly
    return apiFunds;
  }, [apiFunds]);
  
  const {
    data: apiSplits = [],
    isLoading: isLoadingSplits,
    error: splitsError
  } = useFundSplits(clubId || '');

  const {
    data: clubMembers = [],
    isLoading: isLoadingMembers
  } = useClubMembers(clubId || '');

  // Mutation hooks
  const { mutate: updateFund } = useUpdateFund(clubId || '');
  // We'll use isPending directly in the component if needed
  const { mutate: setFundSplits, isPending: isSettingSplits } = useSetFundSplits(clubId || '');
  const { mutate: createFund } = useCreateClubFund(clubId || '');

  // Determine if user is admin
  const isAdmin = clubMembers?.some(member =>
    member.user?.auth0_sub === user?.sub && member.role === ClubRole.Admin
  ) || false;

  // Convert API splits to UI format
  const [uiSplits, setUiSplits] = useState<ExtendedFundSplit[]>([]);
  
  // Dialog states
  const [showCreateFundDialog, setShowCreateFundDialog] = useState(false);
  const [editingFund, setEditingFund] = useState<Fund | null>(null);
  const [showEditFundDialog, setShowEditFundDialog] = useState(false);

  const createFundDialogCloseRef = React.useRef<HTMLButtonElement>(null);
  const editFundDialogCloseRef = React.useRef<HTMLButtonElement>(null);
  
  // Initialize UI splits from API data
  React.useEffect(() => {
    if (apiSplits.length > 0) {
      const convertedSplits = apiSplits.map(split => ({
        fund_id: split.fund_id,
        fund_name: split.fund?.name || 'Unknown Fund',
        split_percentage: split.split_percentage
      }));
      setUiSplits(convertedSplits);
    } else if (funds.length > 0) {
      // If no splits exist yet but we have funds, initialize with active funds at 0%
      const initialSplits = funds
        .filter(fund => fund.is_active)
        .map(fund => ({
          fund_id: fund.id,
          fund_name: fund.name,
          split_percentage: 0
        }));
      setUiSplits(initialSplits);
    }
  }, [apiSplits, funds]);

  const handleCreateFund = (fundData: FundFormData) => {
    console.log('Attempting to create new fund:', fundData);
    createFund(
      { name: fundData.name, description: fundData.description }, // Pass only name and description as per FundCreateData
      {
        onSuccess: (newlyCreatedFund) => {
          toast.success(`Fund "${newlyCreatedFund.name}" created successfully!`);
          setShowCreateFundDialog(false);
          // Query invalidation is handled by the useCreateClubFund hook's onSuccess
        },
        onError: (error: ApiError) => {
          console.error('Error creating fund:', error);
          // Attempt to parse a more specific error message if the backend sends one
          const errorMessage = error.message || 'Failed to create fund.';
          toast.error(errorMessage);
        },
      }
    );
  };

  const handleEditFundTrigger = (fund: Fund) => {
    setEditingFund(fund);
    setShowEditFundDialog(true);
  };

  const handleSaveEditedFund = (updatedData: FundFormData) => {
    if (!editingFund) return;
    console.log('Saving fund:', editingFund.id, updatedData);
    
    // Call the API to update the fund
    updateFund({
      fundId: editingFund.id,
      fundData: updatedData
    }, {
      onSuccess: () => {
        toast.success(`Fund "${updatedData.name}" updated successfully`);
        
        // Update UI splits if fund name changed
        if (editingFund.name !== updatedData.name) {
          setUiSplits(prev =>
            prev.map(s => s.fund_id === editingFund.id
              ? {...s, fund_name: updatedData.name}
              : s
            )
          );
        }
        
        // Handle active/inactive state changes
        const wasActive = editingFund.is_active;
        const nowActive = updatedData.is_active;
        
        if (wasActive && !nowActive) { // Became inactive
          // Remove from UI splits
          setUiSplits(prev => prev.filter(s => s.fund_id !== editingFund.id));
        } else if (!wasActive && nowActive) { // Became active
          // Add to UI splits if not present
          if (!uiSplits.find(s => s.fund_id === editingFund.id)) {
            setUiSplits(prev => [...prev, {
              fund_id: editingFund.id,
              fund_name: updatedData.name,
              split_percentage: 0
            }]);
          }
        }
        
        setShowEditFundDialog(false);
        setEditingFund(null);
      },
      onError: (error) => {
        console.error('Error updating fund:', error);
        toast.error('Failed to update fund');
      }
    });
  };

  const handleSplitChange = (fundId: string, newPercentageStr: string) => {
    // Parse the user input as a whole number percentage (e.g., "50" for 50%)
    let newPercentage = parseFloat(newPercentageStr);
    if (isNaN(newPercentage)) newPercentage = 0;
    newPercentage = Math.max(0, Math.min(100, newPercentage)); // Clamp between 0 and 100

    // Convert to decimal format (e.g., 0.50 for 50%) before storing in state
    setUiSplits(
      uiSplits.map((split) =>
        split.fund_id === fundId ? { ...split, split_percentage: newPercentage / 100 } : split
      )
    );
  };

  // Calculate the total allocated percentage (as a whole number, e.g., 100 for 100%)
  const totalAllocatedPercentage = useMemo(() => {
    return uiSplits.reduce((sum, split) => {
        const fundDetails = funds.find(f => f.id === split.fund_id);
        // Convert from decimal to percentage for display and validation
        return fundDetails?.is_active ? sum + (split.split_percentage * 100) : sum;
    }, 0);
  }, [uiSplits, funds]);

  // Loading state
  const isLoading = isLoadingFunds || isLoadingSplits || isLoadingMembers;
  const error = fundsError || splitsError;
  // Prepare data for rendering
  const activeFundsForSplitTable = funds.filter(f => f.is_active);

  return (
    <div className="space-y-8">
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-slate-600">Loading funds data...</p>
          </div>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg text-center">
          <div className="text-red-500 mb-2">
            <AlertTriangle className="h-10 w-10 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-red-700 mb-2">Error Loading Funds</h3>
          <p className="text-red-600 mb-4">
            There was a problem retrieving the funds data. Please try again later.
          </p>
          <Button variant="outline" className="bg-white border-red-300 text-red-700 hover:bg-red-50">
            Retry
          </Button>
        </div>
      ) : (
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
              {/* We're getting the brokerage cash balance from the portfolio data or the fund data if available */}
            </CardContent>
            <CardFooter className="border-t border-slate-200/75 pt-4 flex gap-2">
              <Button asChild variant="outline" className="flex-1 bg-white hover:bg-slate-50">
                <Link to={`/club/${clubId}/funds/${fund.id}`}>View Details</Link>
              </Button>
              {isAdmin && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-slate-500 hover:text-blue-600 hover:bg-slate-100"
                  onClick={() => handleEditFundTrigger({
                    ...fund,
                    description: fund.description || '' // Ensure description is not undefined
                  })}
                >
                  <Edit3 className="h-5 w-5" /><span className="sr-only">Edit Fund</span>
                </Button>
              )}
            </CardFooter>
          </Card>
        ))}
        {!isLoadingFunds && !fundsError && funds.length === 0 && (
          <Card className="mt-6 col-span-1 md:col-span-2 xl:col-span-3">
            <CardHeader>
              <CardTitle className="text-slate-800">No Funds Found</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600 mb-4">
                This club does not have any investment funds configured yet.
              </p>
              {isAdmin && (
                <Dialog open={showCreateFundDialog} onOpenChange={setShowCreateFundDialog}>
                  <DialogTrigger asChild>
                    <Button className="bg-blue-600 hover:bg-blue-700">
                      <PlusCircle className="mr-2 h-5 w-5" /> Create First Fund
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="sm:max-w-lg bg-white">
                    <DialogHeader>
                      <DialogTitle className="text-slate-800">Create New Fund</DialogTitle>
                      <DialogDescription>Define a new investment fund for your club. New funds are active by default.</DialogDescription>
                    </DialogHeader>
                    {/* Ensure FundDialogForm and its props (handleCreateFund, createFundDialogCloseRef) are correctly used as already defined in the page */}
                    <FundDialogForm
                      mode="create"
                      onSave={handleCreateFund}
                      dialogCloseRef={createFundDialogCloseRef}
                      initialData={{ name: '', description: '', is_active: true }}
                    />
                  </DialogContent>
                </Dialog>
              )}
            </CardContent>
          </Card>
        )}
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
                    initialData={{
                      name: editingFund.name,
                      description: editingFund.description || '',
                      is_active: editingFund.is_active
                    }}
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
                  const split = uiSplits.find((s: ExtendedFundSplit) => s.fund_id === fund.id);
                  return (
                    <TableRow key={fund.id} className="hover:bg-slate-50/50">
                      <TableCell className="font-medium text-slate-800">{fund.name}</TableCell>
                      <TableCell className="text-right">
                        <div className="relative w-24 ml-auto">
                          <Input
                            type="number"
                            value={split ? (split.split_percentage * 100).toString() : '0'}
                            onChange={(e) => handleSplitChange(fund.id, e.target.value)}
                            className="w-full h-9 pr-6 text-right border-slate-300 focus:border-blue-500 focus:ring-blue-500"
                            min="0"
                            max="100"
                            step="0.01"
                            aria-label={`${fund.name} allocation percentage`}
                          />
                          <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
                            <span className="text-slate-500">%</span>
                          </div>
                        </div>
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
              <Button
                className="bg-blue-600 hover:bg-blue-700"
                onClick={() => {
                  // Convert UI splits to API format
                  // Convert UI splits (with split_percentage as decimal) to API format
                  const apiFormatSplits: ApiFundSplit[] = uiSplits
                    .filter(s => activeFundsForSplitTable.find(f => f.id === s.fund_id))
                    .map(s => ({
                      fund_id: s.fund_id,
                      split_percentage: s.split_percentage // Already in decimal format (0-1)
                    }));
                  
                  // Call the API to save fund splits
                  setFundSplits(apiFormatSplits, {
                    onSuccess: () => {
                      toast.success('Fund allocations saved successfully');
                    },
                    onError: (error) => {
                      console.error('Error saving fund splits:', error);
                      toast.error('Failed to save fund allocations');
                    }
                  });
                }}
                disabled={(totalAllocatedPercentage !== 100 && activeFundsForSplitTable.length > 0) || isSettingSplits}
              >
                {isSettingSplits ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" /> Save Allocations
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
      {isAdmin && activeFundsForSplitTable.length === 0 && funds.length > 0 && ( // TODO: Implement UI for when there are no active funds for split table, but inactive funds exist
        null
      )}
        </div>
      )}
    </div>
  );
};

export default FundsPage;
