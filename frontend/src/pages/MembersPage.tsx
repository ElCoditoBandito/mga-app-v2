
// frontend/src/pages/MembersPage.tsx
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
// import { Skeleton } from '@/components/ui/skeleton';
import { UserPlus, Edit2, FileText, UserX, Download, Users as UsersIcon, BookOpenCheck } from 'lucide-react';
import { cn } from '@/lib/utils';

// --- Mock Data Structures ---
interface User {
  id: string;
  name?: string; // Optional display name
  email: string;
}

enum ClubRole {
  ADMIN = 'Admin',
  MEMBER = 'Member',
  READ_ONLY = 'Read-Only',
}

interface ClubMembership {
  id: string;
  user: User;
  role: ClubRole;
  created_at: string; // Date joined
  total_units_held: number; // Calculated from member_transactions
  // current_equity_value would be total_units_held * latest_unit_value
}

interface MembersPageData {
  clubId: string;
  clubName: string;
  memberships: ClubMembership[];
  latest_unit_value: number | null; // Needed to calculate equity
  isAdmin: boolean;
}

// --- Mock Data Generation ---
const MOCK_USERS_MEMBERS_PAGE: User[] = [
  { id: 'user1', name: 'Alice Wonderland', email: 'alice@example.com' },
  { id: 'user2', name: 'Bob The Builder', email: 'bob@example.com' },
  { id: 'user3', email: 'carol@example.com' }, // No name example
];

const MOCK_MEMBERS_PAGE_DATA: MembersPageData = {
  clubId: 'club123',
  clubName: 'Eagle Investors Club',
  isAdmin: true,
  latest_unit_value: 12.503478, // From ClubAccountingPage mock
  memberships: [
    {
      id: 'mem1',
      user: MOCK_USERS_MEMBERS_PAGE[0],
      role: ClubRole.ADMIN,
      created_at: '2023-01-15T10:00:00Z',
      total_units_held: 5000.75,
    },
    {
      id: 'mem2',
      user: MOCK_USERS_MEMBERS_PAGE[1],
      role: ClubRole.MEMBER,
      created_at: '2023-03-20T14:30:00Z',
      total_units_held: 3000.25,
    },
    {
      id: 'mem3',
      user: MOCK_USERS_MEMBERS_PAGE[2],
      role: ClubRole.READ_ONLY,
      created_at: '2024-01-10T09:15:00Z',
      total_units_held: 1000.00,
    },
  ],
};

// --- Helper Functions ---
const formatCurrency = (value?: number | null) => {
  if (value == null) return 'N/A';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
};

const formatNumber = (value?: number | null, precision = 2) => {
  if (value == null) return 'N/A';
  return new Intl.NumberFormat('en-US', { minimumFractionDigits: precision, maximumFractionDigits: precision }).format(value);
};

const formatDate = (dateString?: string) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

// --- Invite Member Dialog ---
interface InviteMemberFormProps {
  onInvite: (email: string, role: ClubRole) => void;
}
const InviteMemberForm: React.FC<InviteMemberFormProps> = ({ onInvite }) => {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<ClubRole>(ClubRole.MEMBER);
  const inviteDialogCloseRef = React.useRef<HTMLButtonElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) {
        alert("Please enter an email address.");
        return;
    }
    onInvite(email, role);
    // Normally, successful invite might close dialog via parent state change
    inviteDialogCloseRef.current?.click(); 
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 pt-2">
      <div>
        <Label htmlFor="inviteEmail">Email Address of Invitee</Label>
        <Input id="inviteEmail" type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="name@example.com" required className="mt-1"/>
      </div>
      <div>
        <Label htmlFor="inviteRole">Assign Role</Label>
        <Select onValueChange={(value) => setRole(value as ClubRole)} defaultValue={ClubRole.MEMBER}>
            <SelectTrigger id="inviteRole" className="mt-1 w-full">
                <SelectValue placeholder="Select a role" />
            </SelectTrigger>
            <SelectContent>
                {/* Admin role typically assigned manually/separately post-invite or by club creator */}
                <SelectItem value={ClubRole.MEMBER}>{ClubRole.MEMBER}</SelectItem>
                <SelectItem value={ClubRole.READ_ONLY}>{ClubRole.READ_ONLY}</SelectItem>
            </SelectContent>
        </Select>
      </div>
      <DialogFooter className="mt-6">
        <DialogClose asChild><Button type="button" variant="outline" ref={inviteDialogCloseRef}>Cancel</Button></DialogClose>
        <Button type="submit" className="bg-blue-600 hover:bg-blue-700">Send Invitation</Button>
      </DialogFooter>
    </form>
  );
};

// --- Main Component ---
const MembersPage = () => {
  const { clubId } = useParams<{ clubId: string }>();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [pageData, _setPageData] = useState<MembersPageData>(MOCK_MEMBERS_PAGE_DATA);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [isLoading, _setIsLoading] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [error, _setError] = useState<Error | null>(null);
  const [showInviteDialog, setShowInviteDialog] = useState(false);

  const handleInviteMember = (email: string, role: ClubRole) => {
    console.log(`Inviting member: ${email} with role: ${role} to club ${clubId}`);
    // API call to backend to handle invitation logic
    // For mock, perhaps add to a "pending invitations" list if we had one.
    setShowInviteDialog(false); // Close dialog on submission for now
  };
  
  // Placeholder for actions
  const handleEditRole = (memberId: string) => console.log('Edit role for:', memberId);
  const handleViewStatement = (memberId: string) => console.log('View statement for:', memberId);
  const handleRemoveMember = (memberId: string) => console.log('Remove member:', memberId);

  if (isLoading) { /* Skeleton */ }
  if (error || !pageData) { /* Error */ }

  const { memberships, latest_unit_value, isAdmin } = pageData;

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Club Members</h1>
          <p className="text-slate-600">Manage club members, view their roles, and see their equity.</p>
        </div>
        {isAdmin && (
            <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
                <DialogTrigger asChild>
                    <Button className="bg-blue-600 hover:bg-blue-700">
                        <UserPlus className="mr-2 h-5 w-5" /> Invite New Member
                    </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md bg-white">
                    <DialogHeader>
                        <DialogTitle className="text-slate-800">Invite New Member</DialogTitle>
                        <DialogDescription>Enter the email address and assign a role for the new member.</DialogDescription>
                    </DialogHeader>
                    <InviteMemberForm onInvite={handleInviteMember} />
                </DialogContent>
            </Dialog>
        )}
      </div>

      {/* Section 2: Members Table */}
      <Card className="bg-white border-slate-200/75 shadow-sm">
        <CardHeader>
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <div>
                <CardTitle className="text-lg font-medium text-slate-800">Current Members ({memberships.length})</CardTitle>
                <CardDescription className="text-sm text-slate-600">List of all active members in the club.</CardDescription>
            </div>
            <Button variant="outline" size="sm" className="bg-white"><Download className="mr-2 h-4 w-4"/> Export Member List</Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {memberships.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-[25%]">Name/Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Date Joined</TableHead>
                  <TableHead className="text-right">Total Units Held</TableHead>
                  <TableHead className="text-right">Current Equity Value</TableHead>
                  {isAdmin && <TableHead className="text-center w-[120px]">Actions</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {memberships.map(mem => {
                  const equityValue = latest_unit_value ? mem.total_units_held * latest_unit_value : null;
                  return (
                    <TableRow key={mem.id} className="hover:bg-slate-50/50 text-sm">
                      <TableCell>
                        <div className="font-medium text-slate-800">{mem.user.name || '-'}</div>
                        <div className="text-xs text-slate-500">{mem.user.email}</div>
                      </TableCell>
                      <TableCell>
                        <span className={cn("px-2 py-0.5 rounded-full text-xs font-semibold",
                            mem.role === ClubRole.ADMIN ? "bg-purple-100 text-purple-700" :
                            mem.role === ClubRole.MEMBER ? "bg-blue-100 text-blue-700" :
                            "bg-slate-100 text-slate-600"
                        )}>{mem.role}</span>
                      </TableCell>
                      <TableCell className="text-slate-600">{formatDate(mem.created_at)}</TableCell>
                      <TableCell className="text-right font-medium text-slate-700">{formatNumber(mem.total_units_held, 4)}</TableCell>
                      <TableCell className="text-right font-semibold text-blue-600">{formatCurrency(equityValue)}</TableCell>
                      {isAdmin && (
                        <TableCell className="text-center space-x-1">
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-500 hover:text-blue-600" onClick={() => handleEditRole(mem.id)} title="Edit Role"><Edit2 className="h-4 w-4"/></Button>
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-500 hover:text-blue-600" onClick={() => handleViewStatement(mem.id)} title="View Statement"><FileText className="h-4 w-4"/></Button>
                          <Button variant="ghost" size="icon" className="h-7 w-7 text-red-500 hover:text-red-700 hover:bg-red-100/50" onClick={() => handleRemoveMember(mem.id)} title="Remove Member"><UserX className="h-4 w-4"/></Button>
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-10">
                <UsersIcon className="mx-auto h-12 w-12 text-slate-400" />
                <h3 className="mt-2 text-sm font-medium text-slate-900">No members found</h3>
                <p className="mt-1 text-sm text-slate-500">Get started by inviting the first member to the club.</p>
                {isAdmin && (
                    <DialogTrigger asChild>
                        <Button className="mt-4 bg-blue-600 hover:bg-blue-700">
                            <UserPlus className="mr-2 h-4 w-4" /> Invite New Member
                        </Button>
                    </DialogTrigger>
                )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Future Section: Pending Invitations - Placeholder */}
      {isAdmin && (
        <Card className="bg-white border-slate-200/75 shadow-sm">
            <CardHeader>
                <CardTitle className="text-lg font-medium text-slate-800">Pending Invitations</CardTitle>
                <CardDescription className="text-sm text-slate-600">Invitations that have been sent but not yet accepted.</CardDescription>
            </CardHeader>
            <CardContent className="h-24 flex items-center justify-center bg-slate-50 rounded-lg">
                <BookOpenCheck className="h-8 w-8 text-slate-400 mr-3" />
                <p className="text-slate-500">Pending invitations feature will be available in a future update.</p>
            </CardContent>
        </Card>
      )}

    </div>
  );
};

export default MembersPage;
