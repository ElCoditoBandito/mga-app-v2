
// frontend/src/pages/ClubAccountingPage.tsx
import React, { useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose
} from '@/components/ui/dialog';
// import { Skeleton } from '@/components/ui/skeleton';
import { DollarSign, BookOpen, TrendingUp, Users, Receipt, Gift, RefreshCw, Download, Banknote, ArrowRightLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

// Import Forms
import RecordMemberTransactionForm, { MemberTransactionFormData } from '@/components/forms/RecordMemberTransactionForm';
import LogClubExpenseForm, { ClubExpenseFormData } from '@/components/forms/LogClubExpenseForm';
import LogCashTransferForm, { CashTransferFormData, CashTransferType } from '@/components/forms/LogCashTransferForm';

// --- Mock Data Structures & Generation (simplified, ensure alignment with previous definitions) ---
interface UserSlim {
  id: string;
  email: string;
  name?: string; // For display in RecordMemberTransactionForm
}
interface MemberTransaction { id: string; user: UserSlim; transaction_type: 'DEPOSIT' | 'WITHDRAWAL'; transaction_date: string; amount: number; notes?: string; units_transacted?: number; unit_value_used?: number;}
interface ClubLevelTransaction { id: string; transaction_date: string; transaction_type: 'CLUB_EXPENSE' | 'BANK_INTEREST' | 'BANK_TO_BROKERAGE' | 'BROKERAGE_TO_BANK'; description: string; total_amount: number; fund_name?: string;}
interface UnitValueHistory { id: string; valuation_date: string; total_club_value: number; total_units_outstanding: number; unit_value: number;}
interface ClubAccountingPageData {
  clubId: string; clubName: string; club_bank_account_balance: number;
  latest_unit_value_record: UnitValueHistory | null;
  member_transactions: MemberTransaction[];
  club_level_transactions: ClubLevelTransaction[];
  unit_value_history: UnitValueHistory[];
  isAdmin: boolean;
  membersForForm: UserSlim[]; // For member transaction form
  fundsForForm: {id: string, name: string}[]; // For cash transfer form
}
type BankLedgerItem = ({ itemType: 'MemberTransaction' } & MemberTransaction) | ({ itemType: 'ClubLevelTransaction' } & ClubLevelTransaction);

const MOCK_USERS_SLIM_ACC: UserSlim[] = [
    { id: 'user1', email: 'alice@example.com', name: 'Alice W.' },
    { id: 'user2', email: 'bob@example.com', name: 'Bob B.' },
];
const MOCK_FUNDS_SLIM_ACC: {id: string, name: string}[] = [
    { id: 'fundA', name: 'US Equities Fund' }, { id: 'fundB', name: 'Global Growth Fund' }
];

const MOCK_CLUB_ACCOUNTING_DATA_STORE: { current: ClubAccountingPageData } = {
    current: {
        clubId: 'club123',
        clubName: 'Eagle Investors Club',
        isAdmin: true,
        club_bank_account_balance: 25034.78,
        latest_unit_value_record: { id: 'uvh10', valuation_date: '2024-07-28', total_club_value: 125034.78, total_units_outstanding: 10000, unit_value: 12.503478 },
        member_transactions: [
            { id: 'mt1', user: MOCK_USERS_SLIM_ACC[0], transaction_type: 'DEPOSIT', transaction_date: '2024-07-25', amount: 1000, notes: 'Initial contribution'},
        ],
        club_level_transactions: [
            { id: 'clt1', transaction_date: '2024-07-28', transaction_type: 'CLUB_EXPENSE', description: 'Annual Accounting Software', total_amount: -75.00 },
        ],
        unit_value_history: [
            { id: 'uvh10', valuation_date: '2024-07-28', total_club_value: 125034.78, total_units_outstanding: 10000, unit_value: 12.503478 },
        ],
        membersForForm: MOCK_USERS_SLIM_ACC,
        fundsForForm: MOCK_FUNDS_SLIM_ACC,
    }
};

// --- Helper Functions (Simplified) ---
const formatCurrency = (value?: number | null, withSign=false) => value != null ? new Intl.NumberFormat('en-US', {style:'currency', currency:'USD', signDisplay: withSign ? 'exceptZero' : 'auto'}).format(value) : 'N/A';
const formatNumber = (value?: number | null, precision=2) => value != null ? value.toFixed(precision) : 'N/A';
const formatDate = (dateString?: string) => dateString ? new Date(dateString).toLocaleDateString('en-US', {month:'short',day:'numeric',year:'numeric'}) : 'N/A';

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
  const { clubId = "club123" } = useParams<{ clubId: string }>();
  const [pageData, setPageData] = useState<ClubAccountingPageData>(MOCK_CLUB_ACCOUNTING_DATA_STORE.current);
  
  // Dialog states
  const [showLogInterestDialog, setShowLogInterestDialog] = useState(false);
  const [showRecordMemberTxDialog, setShowRecordMemberTxDialog] = useState(false);
  const [showLogExpenseDialog, setShowLogExpenseDialog] = useState(false);
  const [showLogCashTransferDialog, setShowLogCashTransferDialog] = useState(false);

  const combinedLedgerItems = useMemo(() => { /* ... same as before ... */ 
    if (!pageData) return [];
    const items: BankLedgerItem[] = [
      ...pageData.member_transactions.map(tx => ({ ...tx, itemType: 'MemberTransaction' as const })),
      ...pageData.club_level_transactions.map(tx => ({ ...tx, itemType: 'ClubLevelTransaction' as const })),
    ];
    return items.sort((a, b) => new Date(b.transaction_date).getTime() - new Date(a.transaction_date).getTime());
  }, [pageData]);

  // Mock Handlers
  const handleAddClubLevelTransaction = (newTxData: Omit<ClubLevelTransaction, 'id'>) => {
    const newTx: ClubLevelTransaction = { ...newTxData, id: `clt${Math.random().toString(16).slice(2)}` };
    setPageData(prev => prev ? ({ ...prev, club_level_transactions: [newTx, ...prev.club_level_transactions] }) : null);
  };
  const handleAddMemberTransaction = (newTxData: Omit<MemberTransaction, 'id' | 'user'> & {user_id: string}) => {
    const user = MOCK_USERS_SLIM_ACC.find(u => u.id === newTxData.user_id) || MOCK_USERS_SLIM_ACC[0];
    const newTx: MemberTransaction = { ...newTxData, id: `mt${Math.random().toString(16).slice(2)}`, user };
    setPageData(prev => prev ? ({ ...prev, member_transactions: [newTx, ...prev.member_transactions] }) : null);
  };

  const handleLogBankInterestSubmit = async (data: { date: string; amount: number; notes?: string }) => {
    console.log('Log Bank Interest Submitted:', data);
    handleAddClubLevelTransaction({transaction_date: data.date, transaction_type: 'BANK_INTEREST', description: data.notes || 'Bank Interest', total_amount: data.amount});
    setShowLogInterestDialog(false);
  };

  const handleRecordMemberTxSubmit = async (data: MemberTransactionFormData) => {
    console.log('Member Transaction Submitted:', data);
    handleAddMemberTransaction(data);
    setShowRecordMemberTxDialog(false);
  };

  const handleLogExpenseSubmit = async (data: ClubExpenseFormData) => {
    console.log('Club Expense Submitted:', data);
    handleAddClubLevelTransaction({transaction_date: data.transaction_date, transaction_type: 'CLUB_EXPENSE', description: data.description, total_amount: -Math.abs(data.total_amount), fees_commissions: data.fees_commissions});
    setShowLogExpenseDialog(false);
  };
  
  const handleLogCashTransferSubmit = async (data: CashTransferFormData) => {
    console.log('Cash Transfer Submitted:', data);
    // This might create one or two ClubLevelTransactions depending on type
    // Example: BANK_TO_BROKERAGE reduces bank balance
    handleAddClubLevelTransaction({transaction_date: data.transaction_date, transaction_type: data.transaction_type, description: data.description || 'Cash Transfer', total_amount: (data.transaction_type === CashTransferType.BROKERAGE_TO_BANK ? 1 : -1) * data.total_amount, fund_name: data.fund_id ? pageData.fundsForForm.find(f=>f.id === data.fund_id)?.name : undefined});
    setShowLogCashTransferDialog(false);
  };

  if (!pageData) return <div>Loading or error...</div>; // Simplified loading/error
  const { club_bank_account_balance, latest_unit_value_record, unit_value_history, isAdmin, membersForForm, fundsForForm } = pageData;

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Club Accounting & Banking</h1>
      {/* Section 1: Key Club Financials - unchanged */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card className="bg-white border-slate-200/75 shadow-sm"><CardHeader className="pb-1.5"><CardTitle className="text-[0.7rem] font-medium text-slate-500 uppercase tracking-wider flex justify-between items-center">Club Bank Balance <Banknote className="h-4 w-4 text-slate-400" /></CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-slate-900">{formatCurrency(club_bank_account_balance)}</div></CardContent></Card>
        <Card className="bg-white border-slate-200/75 shadow-sm"><CardHeader className="pb-1.5"><CardTitle className="text-[0.7rem] font-medium text-slate-500 uppercase tracking-wider flex justify-between items-center">Latest Unit Value <TrendingUp className="h-4 w-4 text-slate-400" /></CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-slate-900">{formatCurrency(latest_unit_value_record?.unit_value, true)?.substring(0,10)}</div><p className="text-xs text-slate-500">As of {formatDate(latest_unit_value_record?.valuation_date)}</p></CardContent></Card>
        <Card className="bg-white border-slate-200/75 shadow-sm"><CardHeader className="pb-1.5"><CardTitle className="text-[0.7rem] font-medium text-slate-500 uppercase tracking-wider flex justify-between items-center">Total Units <BookOpen className="h-4 w-4 text-slate-400" /></CardTitle></CardHeader><CardContent><div className="text-2xl font-bold text-slate-900">{formatNumber(latest_unit_value_record?.total_units_outstanding)}</div><p className="text-xs text-slate-500">As of {formatDate(latest_unit_value_record?.valuation_date)}</p></CardContent></Card>
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
                    <DialogContent className="sm:max-w-lg bg-white p-6"><RecordMemberTransactionForm clubId={clubId} members={membersForForm} latestUnitValue={latest_unit_value_record?.unit_value} latestValuationDate={latest_unit_value_record?.valuation_date} onSubmit={handleRecordMemberTxSubmit} onCancel={()=>setShowRecordMemberTxDialog(false)}/></DialogContent>
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
                    <DialogContent className="sm:max-w-xl bg-white p-6"><LogCashTransferForm clubId={clubId} funds={fundsForForm} onSubmit={handleLogCashTransferSubmit} onCancel={()=>setShowLogCashTransferDialog(false)} /></DialogContent>
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
                        typeLabel = item.transaction_type === 'DEPOSIT' ? 'Deposit' : 'Withdrawal';
                        description = `${item.user.email}`;
                        if(item.transaction_type === 'DEPOSIT') credited = item.amount; else debited = item.amount;
                      } else { 
                        typeLabel = item.transaction_type.replace(/_/g, ' ');
                        description = item.description;
                        if(item.total_amount < 0) debited = Math.abs(item.total_amount); else credited = item.total_amount;
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
            <Card className="bg-white border-slate-200/75 shadow-sm"><CardHeader><div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3"><div><CardTitle className="text-lg font-medium text-slate-800">Club Unit Value History</CardTitle><CardDescription className="text-sm text-slate-600">Historical record of the club's unit valuations.</CardDescription></div><div className="flex gap-2">{isAdmin && <Button variant="outline" size="sm" className="bg-white"><RefreshCw className="mr-2 h-4 w-4"/> Recalculate Unit Value</Button>}<Button variant="outline" size="sm" className="bg-white"><Download className="mr-2 h-4 w-4"/> Export History</Button></div></div></CardHeader><CardContent className="p-0">{unit_value_history.length > 0 ? (<Table><TableHeader><TableRow className="hover:bg-transparent"><TableHead>Valuation Date</TableHead><TableHead className="text-right">Total Club Value</TableHead><TableHead className="text-right">Total Units</TableHead><TableHead className="text-right">Calculated Unit Value</TableHead></TableRow></TableHeader><TableBody>{unit_value_history.map(uv => (<TableRow key={uv.id} className="hover:bg-slate-50/50 text-sm"><TableCell className="font-medium text-slate-700">{formatDate(uv.valuation_date)}</TableCell><TableCell className="text-right text-slate-600">{formatCurrency(uv.total_club_value)}</TableCell><TableCell className="text-right text-slate-600">{formatNumber(uv.total_units_outstanding, 4)}</TableCell><TableCell className="text-right font-semibold text-slate-800">{formatCurrency(uv.unit_value, true)?.substring(0,12)}</TableCell></TableRow>))}</TableBody></Table>) : (<p className="text-center py-6 text-slate-500">No unit value history available.</p>)}</CardContent></Card>
        </TabsContent>
      </Tabs>

      {/* Section 3: Expense Reporting (Placeholder) - unchanged */}
       <Card className="bg-white border-slate-200/75 shadow-sm"><CardHeader><CardTitle className="text-lg font-medium text-slate-800">Club Expenses Summary</CardTitle><CardDescription className="text-sm text-slate-600">Overview of club expenses (YTD, by category - Post-MVP).</CardDescription></CardHeader><CardContent className="h-32 flex items-center justify-center bg-slate-50 rounded-lg"><Receipt className="h-8 w-8 text-slate-400 mr-3" /><p className="text-slate-500">Expense reporting and categorization will be available in a future update.</p></CardContent></Card>
    </div>
  );
};

export default ClubAccountingPage;
