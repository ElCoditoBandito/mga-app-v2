// frontend/src/pages/ClubAccountingPage.tsx
import React, { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose
} from '@/components/ui/dialog';
import { BookOpen, TrendingUp, Users, Receipt, Gift, RefreshCw, Download, Banknote, ArrowRightLeft, Loader2 } from 'lucide-react';
import { useAuth0 } from '@auth0/auth0-react';
import { toast } from 'sonner';

// Import Forms
import RecordMemberTransactionForm from '@/components/forms/RecordMemberTransactionForm';
import type { MemberTransactionFormData } from '@/components/forms/RecordMemberTransactionForm';
import LogClubExpenseForm from '@/components/forms/LogClubExpenseForm';
import type { ClubExpenseFormData } from '@/components/forms/LogClubExpenseForm';
import LogCashTransferForm from '@/components/forms/LogCashTransferForm';
import type { CashTransferFormData } from '@/components/forms/LogCashTransferForm';
import { MemberTransactionType } from '@/enums';

// --- Type Definitions ---
// Using types and hooks from useApi.ts
import {
  useClubDetails,
  useClubMembers,
  useMemberTransactions,
  useFundTransactions,
  useClubFunds,
  useRecordMemberDeposit,
  useRecordMemberWithdrawal,
  useRecordCashReceipt,
  useRecordCashTransfer,
  useRecordClubExpense
} from '@/hooks/useApi';

import type {
  MemberTransaction,
  Transaction,
  ClubMembership,
  Fund
} from '@/lib/apiClient';

// Local interface for combined ledger items
// Extended Transaction type to handle both backend and frontend field names
interface ExtendedTransaction extends Transaction {
  total_amount?: number;
  description?: string;
}

type BankLedgerItem =
  | ({ itemType: 'MemberTransaction' } & MemberTransaction)
  | ({ itemType: 'ClubLevelTransaction' } & ExtendedTransaction);

// --- Helper Functions ---
const formatCurrency = (value?: number | null, withSign=false) => 
  value != null ? new Intl.NumberFormat('en-US', {
    style:'currency', 
    currency:'USD', 
    signDisplay: withSign ? 'exceptZero' : 'auto'
  }).format(value) : 'N/A';

const formatNumber = (value?: number | null, precision=2) => 
  value != null ? value.toFixed(precision) : 'N/A';

const formatDate = (dateString?: string) => 
  dateString ? new Date(dateString).toLocaleDateString('en-US', {
    month:'short',
    day:'numeric',
    year:'numeric'
  }) : 'N/A';

// --- Log Bank Interest Dialog Form (simplified, as it's small and specific) ---
interface LogBankInterestFormProps { onSave: (data: { date: string; amount: number; notes?: string }) => void; }
const LogBankInterestForm: React.FC<LogBankInterestFormProps> = ({ onSave }) => {
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [amount, setAmount] = useState('');
  const [notes, setNotes] = useState('');
  const handleSubmit = (e: React.FormEvent) => { e.preventDefault(); const numAmount = parseFloat(amount); if(isNaN(numAmount) || numAmount <= 0) { alert('Valid positive amount required.'); return; } onSave({ date, amount: numAmount, notes }); };
  return (<form onSubmit={handleSubmit} className="space-y-4 pt-2"><div><Label htmlFor="intDate">Date</Label><Input id="intDate" type="date" value={date} onChange={e=>setDate(e.target.value)} required className="mt-1"/></div><div><Label htmlFor="intAmount">Amount</Label><Input id="intAmount" type="number" value={amount} onChange={e=>setAmount(e.target.value)} placeholder="0.00" step=".01" min=".01" required className="mt-1"/></div><div><Label htmlFor="intNotes">Notes</Label><Textarea id="intNotes" value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Optional notes" rows={2} className="mt-1"/></div><DialogFooter className="mt-6"><DialogClose asChild><Button type="button" variant="outline">Cancel</Button></DialogClose><Button type="submit" className="bg-blue-600 hover:bg-blue-700">Log Interest</Button></DialogFooter></form>);
};

// --- Main Component ---
const ClubAccountingPage = () => {
  const { clubId = "" } = useParams<{ clubId: string }>();
  const { user } = useAuth0();
  
  // Dialog states
  const [showLogInterestDialog, setShowLogInterestDialog] = useState(false);
  const [showRecordMemberTxDialog, setShowRecordMemberTxDialog] = useState(false);
  const [showLogExpenseDialog, setShowLogExpenseDialog] = useState(false);
  const [showLogCashTransferDialog, setShowLogCashTransferDialog] = useState(false);

  // Fetch data using React Query hooks
  const { data: clubData, isLoading: isLoadingClub } = useClubDetails(clubId);
  const { data: members = [], isLoading: isLoadingMembers } = useClubMembers(clubId);
  const { data: memberTransactions = [], isLoading: isLoadingMemberTx } = useMemberTransactions(clubId);
  const { data: funds = [], isLoading: isLoadingFunds } = useClubFunds(clubId);
  
  // For now, we'll fetch all transactions across all funds
  // In a more refined implementation, we might want to filter by transaction types
  const { data: clubTransactions = [], isLoading: isLoadingTransactions } = 
    useFundTransactions(clubId);
  
  // Mutation hooks
  const { mutate: recordMemberDeposit } = useRecordMemberDeposit(clubId);
  const { mutate: recordMemberWithdrawal } = useRecordMemberWithdrawal(clubId);
  const { mutate: recordCashReceipt } = useRecordCashReceipt(clubId);
  const { mutate: recordCashTransfer } = useRecordCashTransfer(clubId);
  const { mutate: recordClubExpenseMutation } = useRecordClubExpense(clubId);
  
  // Determine if user is admin
  const isAdmin = members?.some(member =>
    member.user?.auth0_sub === user?.sub && member.role === 'Admin'
  ) || false;

  // Get latest unit value record - this would ideally come from an API endpoint
  // For a new club, initialize with empty values
  const latestUnitValueRecord = useMemo(() => {
    // Check if this is a new club (no transactions)
    const isNewClub = memberTransactions.length === 0 && clubTransactions.length === 0;
    
    if (isNewClub) {
      return {
        id: 'latest',
        fund_id: '',
        date: new Date().toISOString().split('T')[0],
        unit_value: 0,
        total_units: 0,
        total_value: 0
      };
    } else {
      // For existing clubs, use the mock data for now
      // This would be replaced with actual API data in a future iteration
      return {
        id: 'latest',
        fund_id: '',
        date: new Date().toISOString().split('T')[0],
        unit_value: 12.50,
        total_units: 10000,
        total_value: 125000
      };
    }
  }, [memberTransactions, clubTransactions]);

  // Bank balance now comes directly from the backend via clubData.bank_account_balance

  // Prepare members for form
  const membersForForm = useMemo(() => {
    return members.map((member: ClubMembership) => ({
      id: member.user_id,
      name: member.user ? `${member.user.first_name} ${member.user.last_name}` : member.user_id,
      email: member.user?.email || ''
    }));
  }, [members]);

  // Prepare funds for form
  const fundsForForm = useMemo(() => {
    return funds.map((fund: Fund) => ({
      id: fund.id,
      name: fund.name
    }));
  }, [funds]);

  // Combine member transactions and club transactions for the ledger
  const combinedLedgerItems = useMemo(() => {
    // Create a type-safe array of ledger items
    const memberItems = memberTransactions.map((tx: MemberTransaction) => ({
      ...tx,
      itemType: 'MemberTransaction' as const
    }));
    
    const transactionItems = clubTransactions
      .filter((tx: Transaction) => ['ClubExpense', 'BankInterest', 'BankToBrokerage', 'BrokerageToBank']
        .includes(tx.transaction_type))
      .map((tx: Transaction) => ({
        ...tx,
        itemType: 'ClubLevelTransaction' as const
      }));
    
    const items: BankLedgerItem[] = [...memberItems, ...transactionItems];
    
    return items.sort((a, b) => {
      // Safely get dates for comparison
      const dateA = a.itemType === 'MemberTransaction'
        ? a.transaction_date || ''
        : a.transaction_date || '';
      
      const dateB = b.itemType === 'MemberTransaction'
        ? b.transaction_date || ''
        : b.transaction_date || '';
        
      return new Date(dateB).getTime() - new Date(dateA).getTime();
    }
    );
  }, [memberTransactions, clubTransactions]);

  // Loading state
  const isLoading = isLoadingClub || isLoadingMembers || isLoadingMemberTx || 
                   isLoadingFunds || isLoadingTransactions;

  const handleLogBankInterestSubmit = async (data: { date: string; amount: number; notes?: string }) => {
    console.log('Log Bank Interest Submitted:', data);
    
    // Use the first fund for bank interest or create a specific endpoint
    if (funds.length > 0) {
      recordCashReceipt({
        fund_id: funds[0].id,
        transaction_type: 'BankInterest',
        transaction_date: data.date,
        amount: data.amount,
        notes: data.notes
      }, {
        onSuccess: () => {
          toast.success('Bank interest recorded successfully');
          setShowLogInterestDialog(false);
        },
        onError: (error: unknown) => {
          console.error('Error recording bank interest:', error);
          toast.error('Failed to record bank interest');
        }
      });
    } else {
      toast.error('No funds available to record bank interest');
    }
  };

  const handleRecordMemberTxSubmit = async (data: MemberTransactionFormData) => {
    console.log('Member Transaction Submitted:', data);
    
    if (data.transaction_type === MemberTransactionType.DEPOSIT) {
      recordMemberDeposit({
        user_id: data.user_id,
        amount: data.amount,
        transaction_date: data.transaction_date,
        notes: data.notes
      }, {
        onSuccess: () => {
          toast.success('Member deposit recorded successfully');
          setShowRecordMemberTxDialog(false);
        },
        onError: (error: unknown) => {
          console.error('Error recording member deposit:', error);
          toast.error('Failed to record member deposit');
        }
      });
    } else {
      recordMemberWithdrawal({
        user_id: data.user_id,
        amount: data.amount,
        transaction_date: data.transaction_date,
        notes: data.notes
      }, {
        onSuccess: () => {
          toast.success('Member withdrawal recorded successfully');
          setShowRecordMemberTxDialog(false);
        },
        onError: (error: unknown) => {
          console.error('Error recording member withdrawal:', error);
          toast.error('Failed to record member withdrawal');
        }
      });
    }
  };

  const handleLogExpenseSubmit = async (data: ClubExpenseFormData) => {
    console.log('Club Expense Submitted:', data);
    
    recordClubExpenseMutation({
      transaction_type: 'ClubExpense',
      transaction_date: data.transaction_date,
      total_amount: data.total_amount, // Pass the positive value as entered by the user
      description: data.description,
      fees_commissions: data.fees_commissions
    }, {
      onSuccess: () => {
        toast.success('Club expense recorded successfully');
        setShowLogExpenseDialog(false);
      },
      onError: (error: unknown) => {
        console.error('Error recording club expense:', error);
        toast.error('Failed to record club expense');
      }
    });
  };

  const handleLogCashTransferSubmit = async (data: CashTransferFormData) => {
    console.log('Cash Transfer Submitted:', data);
    
    recordCashTransfer({
      transaction_type: data.transaction_type,
      transaction_date: data.transaction_date,
      total_amount: data.total_amount, // Using 'total_amount' to match updated API interface
      fund_id: data.fund_id,
      target_fund_id: data.target_fund_id, // Add target_fund_id for INTERFUND transfers
      notes: data.description
    }, {
      onSuccess: () => {
        toast.success('Cash transfer recorded successfully');
        setShowLogCashTransferDialog(false);
      },
      onError: (error: unknown) => {
        console.error('Error recording cash transfer:', error);
        toast.error('Failed to record cash transfer');
      }
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading accounting data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Club Accounting & Banking</h1>
      {/* Section 1: Key Club Financials - unchanged */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card className="bg-white border-slate-200/75 shadow-sm">
          <CardHeader className="pb-1.5">
            <CardTitle className="text-[0.7rem] font-medium text-slate-500 uppercase tracking-wider flex justify-between items-center">
              Club Bank Balance <Banknote className="h-4 w-4 text-slate-400" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">{formatCurrency(clubData?.bank_account_balance)}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-white border-slate-200/75 shadow-sm">
          <CardHeader className="pb-1.5">
            <CardTitle className="text-[0.7rem] font-medium text-slate-500 uppercase tracking-wider flex justify-between items-center">
              Latest Unit Value <TrendingUp className="h-4 w-4 text-slate-400" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">
              {formatCurrency(latestUnitValueRecord?.unit_value, true)?.substring(0,10)}
            </div>
            <p className="text-xs text-slate-500">As of {formatDate(latestUnitValueRecord?.date)}</p>
          </CardContent>
        </Card>
        
        <Card className="bg-white border-slate-200/75 shadow-sm">
          <CardHeader className="pb-1.5">
            <CardTitle className="text-[0.7rem] font-medium text-slate-500 uppercase tracking-wider flex justify-between items-center">
              Total Units <BookOpen className="h-4 w-4 text-slate-400" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900">{formatNumber(latestUnitValueRecord?.total_units)}</div>
            <p className="text-xs text-slate-500">As of {formatDate(latestUnitValueRecord?.date)}</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="bank_ledger" className="w-full">
        <TabsList className="grid w-full grid-cols-2 md:w-[400px] bg-slate-200/80">
          <TabsTrigger value="bank_ledger">Bank Account Ledger</TabsTrigger>
          <TabsTrigger value="unit_value_history">Unit Value History</TabsTrigger>
        </TabsList>

        <TabsContent value="bank_ledger" className="mt-4">
          <Card className="bg-white border-slate-200/75 shadow-sm">
            <CardHeader>
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                <CardTitle className="text-lg font-medium text-slate-800">Club Bank Transactions</CardTitle>
                <Button variant="outline" size="sm" className="bg-white"><Download className="mr-2 h-4 w-4" /> Export Ledger</Button>
              </div>
              {isAdmin && (
                <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
                  {/* Record Member D/W Dialog Trigger */}
                  <Dialog open={showRecordMemberTxDialog} onOpenChange={setShowRecordMemberTxDialog}>
                    <DialogTrigger asChild><Button variant="outline" className="bg-white text-sm w-full justify-start"><Users className="mr-2 h-4 w-4 text-blue-600"/>Record Member D/W</Button></DialogTrigger>
                    <DialogContent className="sm:max-w-lg bg-white p-6">
                      <RecordMemberTransactionForm 
                        clubId={clubId} 
                        members={membersForForm} 
                        latestUnitValue={latestUnitValueRecord?.unit_value} 
                        latestValuationDate={latestUnitValueRecord?.date} 
                        onSubmit={handleRecordMemberTxSubmit} 
                        onCancel={()=>setShowRecordMemberTxDialog(false)}
                      />
                    </DialogContent>
                  </Dialog>
                  {/* Log Club Expense Dialog Trigger */}
                  <Dialog open={showLogExpenseDialog} onOpenChange={setShowLogExpenseDialog}>
                    <DialogTrigger asChild><Button variant="outline" className="bg-white text-sm w-full justify-start"><Receipt className="mr-2 h-4 w-4 text-blue-600"/>Log Club Expense</Button></DialogTrigger>
                    <DialogContent className="sm:max-w-lg bg-white p-6"><LogClubExpenseForm clubId={clubId} onSubmit={handleLogExpenseSubmit} onCancel={()=>setShowLogExpenseDialog(false)}/></DialogContent>
                  </Dialog>
                  {/* Log Bank Interest Dialog (already integrated) */}
                  <Dialog open={showLogInterestDialog} onOpenChange={setShowLogInterestDialog}>
                    <DialogTrigger asChild><Button variant="outline" className="bg-white text-sm w-full justify-start"><Gift className="mr-2 h-4 w-4 text-blue-600"/>Log Bank Interest</Button></DialogTrigger>
                    <DialogContent className="sm:max-w-md bg-white p-6"><DialogHeader><DialogTitle>Log Bank Interest Received</DialogTitle></DialogHeader><LogBankInterestForm onSave={handleLogBankInterestSubmit} /></DialogContent>
                  </Dialog>
                  {/* Log Cash Transfer Dialog Trigger */}
                  <Dialog open={showLogCashTransferDialog} onOpenChange={setShowLogCashTransferDialog}>
                    <DialogTrigger asChild><Button variant="outline" className="bg-white text-sm w-full justify-start"><ArrowRightLeft className="mr-2 h-4 w-4 text-blue-600"/>Transfer Cash</Button></DialogTrigger>
                    <DialogContent className="sm:max-w-xl bg-white p-6">
                      <LogCashTransferForm 
                        clubId={clubId} 
                        funds={fundsForForm} 
                        onSubmit={handleLogCashTransferSubmit} 
                        onCancel={()=>setShowLogCashTransferDialog(false)} 
                      />
                    </DialogContent>
                  </Dialog>
                </div>
              )}
            </CardHeader>
            <CardContent className="p-0">
              {/* ... Ledger Table ... unchanged */}
              {combinedLedgerItems.length > 0 ? (
                <Table>
                  <TableHeader><TableRow className="hover:bg-transparent"><TableHead>Date</TableHead><TableHead>Type</TableHead><TableHead>Description/Member</TableHead><TableHead className="text-right">Debited (-)</TableHead><TableHead className="text-right">Credited (+)</TableHead></TableRow></TableHeader>
                  <TableBody>
                    {combinedLedgerItems.map(item => {
                      let description, debited, credited, typeLabel;
                      if (item.itemType === 'MemberTransaction') {
                        typeLabel = item.transaction_type === MemberTransactionType.DEPOSIT ? 'Deposit' : 'Withdrawal';
                        // MemberTransaction might not have user property directly accessible
                        description = 'Member Transaction';
                        if(item.transaction_type === MemberTransactionType.DEPOSIT) {
                          credited = item.amount;
                        } else {
                          debited = item.amount;
                        }
                      } else { 
                        typeLabel = item.transaction_type.replace(/_/g, ' ');
                        description = item.description || item.notes || 'Cash Transaction';
                        // Handle both amount and total_amount fields for compatibility
                        const transactionAmount = item.total_amount !== undefined ? item.total_amount : item.amount;
                        
                        // BankToBrokerage should always be a debit (money leaving bank account)
                        if(item.transaction_type === 'BankToBrokerage') {
                          debited = Math.abs(transactionAmount);
                          credited = undefined; // Ensure it's not also credited
                        }
                        // BrokerageToBank should always be a credit (money entering bank account)
                        else if(item.transaction_type === 'BrokerageToBank') {
                          credited = Math.abs(transactionAmount);
                          debited = undefined; // Ensure it's not also debited
                        }
                        // ClubExpense should always be a debit
                        else if(item.transaction_type === 'ClubExpense') {
                          debited = Math.abs(transactionAmount);
                          credited = undefined; // Ensure it's not also credited
                        }
                        // For other transaction types, use the sign of the amount
                        else if(transactionAmount < 0) {
                          debited = Math.abs(transactionAmount);
                          credited = undefined; // Ensure it's not also credited
                        } else {
                          credited = transactionAmount;
                          debited = undefined; // Ensure it's not also debited
                        }
                      }
                      return (
                        <TableRow key={`${item.itemType}-${item.id}`} className="hover:bg-slate-50/50 text-sm">
                          <TableCell className="text-slate-600">{formatDate(item.transaction_date)}</TableCell>
                          <TableCell className="font-medium text-slate-700">{typeLabel}</TableCell>
                          <TableCell className="text-slate-600 max-w-[250px] truncate" title={description}>{description}</TableCell>
                          <TableCell className="text-right text-red-600">{debited ? formatCurrency(debited) : '-'}</TableCell>
                          <TableCell className="text-right text-green-600">{credited ? formatCurrency(credited) : '-'}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              ) : (<p className="text-center py-6 text-slate-500">No bank transactions recorded yet.</p>)}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="unit_value_history" className="mt-4">
          {/* ... Unit Value History Table ... unchanged */}
            <Card className="bg-white border-slate-200/75 shadow-sm">
              <CardHeader>
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                  <div>
                    <CardTitle className="text-lg font-medium text-slate-800">Club Unit Value History</CardTitle>
                    <CardDescription className="text-sm text-slate-600">Historical record of the club's unit valuations.</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    {isAdmin && (
                      <Button variant="outline" size="sm" className="bg-white">
                        <RefreshCw className="mr-2 h-4 w-4"/> Recalculate Unit Value
                      </Button>
                    )}
                    <Button variant="outline" size="sm" className="bg-white">
                      <Download className="mr-2 h-4 w-4"/> Export History
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                {/* For now, we'll just show the latest unit value since we don't have a history endpoint */}
                {latestUnitValueRecord ? (
                  <Table>
                    <TableHeader>
                      <TableRow className="hover:bg-transparent">
                        <TableHead>Valuation Date</TableHead>
                        <TableHead className="text-right">Total Club Value</TableHead>
                        <TableHead className="text-right">Total Units</TableHead>
                        <TableHead className="text-right">Calculated Unit Value</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow className="hover:bg-slate-50/50 text-sm">
                        <TableCell className="font-medium text-slate-700">{formatDate(latestUnitValueRecord.date)}</TableCell>
                        <TableCell className="text-right text-slate-600">{formatCurrency(latestUnitValueRecord.total_value)}</TableCell>
                        <TableCell className="text-right text-slate-600">{formatNumber(latestUnitValueRecord.total_units, 4)}</TableCell>
                        <TableCell className="text-right font-semibold text-slate-800">{formatCurrency(latestUnitValueRecord.unit_value, true)?.substring(0,12)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                ) : (
                  <p className="text-center py-6 text-slate-500">No unit value history available.</p>
                )}
              </CardContent>
            </Card>
        </TabsContent>
      </Tabs>

      {/* Section 3: Expense Reporting (Placeholder) - unchanged */}
       <Card className="bg-white border-slate-200/75 shadow-sm"><CardHeader><CardTitle className="text-lg font-medium text-slate-800">Club Expenses Summary</CardTitle><CardDescription className="text-sm text-slate-600">Overview of club expenses (YTD, by category - Post-MVP).</CardDescription></CardHeader><CardContent className="h-32 flex items-center justify-center bg-slate-50 rounded-lg"><Receipt className="h-8 w-8 text-slate-400 mr-3" /><p className="text-slate-500">Expense reporting and categorization will be available in a future update.</p></CardContent></Card>
    </div>
  );
};

export default ClubAccountingPage;
