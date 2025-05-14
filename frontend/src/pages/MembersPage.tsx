// frontend/src/pages/MembersPage.tsx
import React, { useState, useMemo } from 'react';
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
import { UserPlus, Edit2, FileText, UserX, Download, Users as UsersIcon, BookOpenCheck, Loader2, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth0 } from '@auth0/auth0-react';
import { toast } from 'sonner';
import { ClubRole } from '@/enums';

// Import API hooks
import {
  useClubMembers,
  useAddClubMember,
  useUpdateMemberRole,
  useRemoveMember
} from '@/hooks/useApi';

// --- Type Definitions ---

// Helper function to convert API role to display role
const displayRole = (role: string): string => {
  switch (role) {
    case ClubRole.Admin: return 'Admin';
    case ClubRole.Member: return 'Member';
    case ClubRole.ReadOnly: return 'Read-Only';
    default: return role;
  }
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
  const [role, setRole] = useState<ClubRole>(ClubRole.Member);
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
        <Select onValueChange={(value) => setRole(value as ClubRole)} defaultValue={ClubRole.Member}>
            <SelectTrigger id="inviteRole" className="mt-1 w-full">
                <SelectValue placeholder="Select a role" />
            </SelectTrigger>
            <SelectContent>
                {/* Admin role typically assigned manually/separately post-invite or by club creator */}
                <SelectItem value={ClubRole.Member}>{displayRole(ClubRole.Member)}</SelectItem>
                <SelectItem value={ClubRole.ReadOnly}>{displayRole(ClubRole.ReadOnly)}</SelectItem>
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
  const { user } = useAuth0();
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [editingMemberId, setEditingMemberId] = useState<string | null>(null);
  const [newRole, setNewRole] = useState<string>('');

  // Fetch data using React Query hooks
  const {
    data: memberships = [],
    isLoading: isLoadingMembers,
    error: membersError
  } = useClubMembers(clubId || '');

  // In a real implementation, we would use a query to get the latest unit value
  // For now, we'll just use a placeholder
  const isLoadingNav = false;

  // Mutation hooks
  const { mutate: addMember } = useAddClubMember(clubId || '');
  const { mutate: updateRole } = useUpdateMemberRole(clubId || '');
  const { mutate: removeMember } = useRemoveMember(clubId || '');

  // Determine if user is admin
  const isAdmin = memberships?.some(member =>
    member.user?.auth0_sub === user?.sub && member.role === ClubRole.Admin
  ) || false;

  // Get latest unit value from NAV data
  const latest_unit_value = useMemo(() => {
    // Define navData inside the useMemo to avoid dependency issues
    const navData = { unit_value: 12.50 }; // This would come from a proper query in a real implementation
    return navData.unit_value || null;
  }, []);

  // Loading state
  const isLoading = isLoadingMembers || isLoadingNav;
  const error = membersError;

  const handleInviteMember = (email: string, role: ClubRole) => {
    console.log(`Inviting member: ${email} with role: ${role} to club ${clubId}`);
    
    addMember({
      member_email: email,
      role: role.toString()
    }, {
      onSuccess: () => {
        toast.success(`Invitation sent to ${email}`);
        setShowInviteDialog(false);
      },
      onError: (error) => {
        console.error('Error inviting member:', error);
        toast.error('Failed to send invitation');
      }
    });
  };
  
  // Handle role editing
  const handleEditRole = (memberId: string) => {
    const membership = memberships.find(m => m.id === memberId);
    if (membership) {
      setEditingMemberId(memberId);
      setNewRole(membership.role);
    }
  };

  const handleSaveRole = () => {
    if (!editingMemberId || !newRole) return;
    
    updateRole({
      userId: editingMemberId,
      newRole: newRole
    }, {
      onSuccess: () => {
        toast.success('Member role updated successfully');
        setEditingMemberId(null);
      },
      onError: (error) => {
        console.error('Error updating role:', error);
        toast.error('Failed to update member role');
      }
    });
  };

  const handleViewStatement = (memberId: string) => {
    console.log('View statement for:', memberId);
    toast.info('Member statements feature coming soon');
  };

  const handleRemoveMember = (memberId: string) => {
    if (window.confirm('Are you sure you want to remove this member?')) {
      removeMember(memberId, {
        onSuccess: () => {
          toast.success('Member removed successfully');
        },
        onError: (error) => {
          console.error('Error removing member:', error);
          toast.error('Failed to remove member');
        }
      });
    }
  };

  return (
    <div className="space-y-8">
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-slate-600">Loading members data...</p>
          </div>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg text-center">
          <div className="text-red-500 mb-2">
            <AlertTriangle className="h-10 w-10 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-red-700 mb-2">Error Loading Members</h3>
          <p className="text-red-600 mb-4">
            There was a problem retrieving the members data. Please try again later.
          </p>
          <Button variant="outline" className="bg-white border-red-300 text-red-700 hover:bg-red-50">
            Retry
          </Button>
        </div>
      ) : (
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
                  <CardTitle className="text-lg font-medium text-slate-800">Current Members ({memberships?.length || 0})</CardTitle>
                  <CardDescription className="text-sm text-slate-600">List of all active members in the club.</CardDescription>
                </div>
                <Button variant="outline" size="sm" className="bg-white"><Download className="mr-2 h-4 w-4"/> Export Member List</Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {memberships && memberships.length > 0 ? (
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
                      // Calculate units held - in a real implementation, this would come from the API
                      const units = mem.units || 0;
                      const equityValue = latest_unit_value ? units * latest_unit_value : null;
                      
                      return (
                        <TableRow key={mem.id} className="hover:bg-slate-50/50 text-sm">
                          <TableCell>
                            <div className="font-medium text-slate-800">
                              {mem.user ? `${mem.user.first_name || ''} ${mem.user.last_name || ''}`.trim() || '-' : '-'}
                            </div>
                            <div className="text-xs text-slate-500">{mem.user?.email || '-'}</div>
                          </TableCell>
                          <TableCell>
                            {editingMemberId === mem.id ? (
                              <div className="flex items-center space-x-2">
                                <Select value={newRole} onValueChange={setNewRole}>
                                  <SelectTrigger className="h-7 text-xs w-24">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value={ClubRole.Admin}>{displayRole(ClubRole.Admin)}</SelectItem>
                                    <SelectItem value={ClubRole.Member}>{displayRole(ClubRole.Member)}</SelectItem>
                                    <SelectItem value={ClubRole.ReadOnly}>{displayRole(ClubRole.ReadOnly)}</SelectItem>
                                  </SelectContent>
                                </Select>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-7 px-2 text-xs text-green-600"
                                  onClick={handleSaveRole}
                                >
                                  Save
                                </Button>
                              </div>
                            ) : (
                              <span className={cn("px-2 py-0.5 rounded-full text-xs font-semibold",
                                  mem.role === ClubRole.Admin ? "bg-purple-100 text-purple-700" :
                                  mem.role === ClubRole.Member ? "bg-blue-100 text-blue-700" :
                                  "bg-slate-100 text-slate-600"
                              )}>{displayRole(mem.role)}</span>
                            )}
                          </TableCell>
                          <TableCell className="text-slate-600">{formatDate(mem.created_at)}</TableCell>
                          <TableCell className="text-right font-medium text-slate-700">{formatNumber(units, 4)}</TableCell>
                          <TableCell className="text-right font-semibold text-blue-600">{formatCurrency(equityValue)}</TableCell>
                          {isAdmin && (
                            <TableCell className="text-center space-x-1">
                              {editingMemberId !== mem.id && (
                                <Button variant="ghost" size="icon" className="h-7 w-7 text-slate-500 hover:text-blue-600" onClick={() => handleEditRole(mem.id)} title="Edit Role"><Edit2 className="h-4 w-4"/></Button>
                              )}
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
      )}
    </div>
  );
};

export default MembersPage;
