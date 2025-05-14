// frontend/src/pages/ClubSettingsPage.tsx
import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
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
import { Settings, Users, BarChart2, AlertTriangle, Archive, ShieldAlert, Save, ExternalLink, Loader2 } from 'lucide-react';
import { useAuth0 } from '@auth0/auth0-react';
import { toast } from 'sonner';

// Import API hooks
import {
  useClubDetails,
  useClubMembers,
  useUpdateClub
} from '@/hooks/useApi';

// --- Main Component ---
const ClubSettingsPage = () => {
  const { clubId = "" } = useParams<{ clubId: string }>();
  const { user } = useAuth0();

  // Fetch data using React Query hooks
  const { 
    data: club, 
    isLoading: isLoadingClub, 
    error: clubError 
  } = useClubDetails(clubId);

  const { 
    data: members = [], 
    isLoading: isLoadingMembers 
  } = useClubMembers(clubId);

  // Mutation hooks
  const { mutate: updateClub, isPending: isUpdatingClub } = useUpdateClub(clubId);
  
  // Since useCalculateNav doesn't exist yet, we'll create a mock function
  const [isCalculatingNav, setIsCalculatingNav] = useState(false);

  // Form state for General Club Information
  const [clubName, setClubName] = useState(club?.name || '');
  const [clubDescription, setClubDescription] = useState(club?.description || '');

  // Update form values when club data is loaded
  React.useEffect(() => {
    if (club) {
      setClubName(club.name);
      setClubDescription(club.description || '');
    }
  }, [club]);

  const [showArchiveConfirmDialog, setShowArchiveConfirmDialog] = useState(false);
  const [archiveConfirmationText, setArchiveConfirmationText] = useState('');

  // Determine if user is admin
  const isAdmin = members?.some(member =>
    member.user_id === user?.sub && member.role === 'ADMIN'
  ) || false;

  const handleSaveClubDetails = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Saving club details:', { clubId, clubName, clubDescription });
    
    updateClub({
      name: clubName,
      description: clubDescription
    }, {
      onSuccess: () => {
        toast.success('Club details saved successfully');
      },
      onError: (error: unknown) => {
        console.error('Error updating club details:', error);
        toast.error('Failed to save club details');
      }
    });
  };

  const handleTriggerManualValuation = () => {
    console.log('Triggering manual unit value calculation for club:', clubId);
    
    // Mock implementation since we don't have the actual API hook yet
    setIsCalculatingNav(true);
    
    // Simulate API call with a timeout
    setTimeout(() => {
      setIsCalculatingNav(false);
      toast.success('Unit value calculation completed successfully');
    }, 1500);
  };

  const handleArchiveClub = () => {
    if (archiveConfirmationText === `archive ${club?.name}`) {
      console.log('Archiving club:', clubId);
      
      // This would be implemented with a specific API endpoint for archiving
      // For now, we'll just show a toast message
      toast.success(`Club '${club?.name}' archived successfully!`);
      setShowArchiveConfirmDialog(false);
      setArchiveConfirmationText('');
    } else {
      toast.error('Confirmation text does not match. Please type the exact phrase to confirm.');
    }
  };

  // Loading state
  const isLoading = isLoadingClub || isLoadingMembers;
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading club settings...</p>
        </div>
      </div>
    );
  }

  if (clubError || !club) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg text-center">
        <div className="text-red-500 mb-2">
          <AlertTriangle className="h-10 w-10 mx-auto" />
        </div>
        <h3 className="text-lg font-semibold text-red-700 mb-2">Error Loading Club Settings</h3>
        <p className="text-red-600 mb-4">
          There was a problem retrieving the club settings. Please try again later.
        </p>
        <Button variant="outline" className="bg-white border-red-300 text-red-700 hover:bg-red-50">
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">Club Settings</h1>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid w-full grid-cols-2 sm:grid-cols-3 md:grid-cols-5 bg-slate-200/80 h-auto p-1">
          <TabsTrigger value="general" className="text-xs sm:text-sm data-[state=active]:bg-white data-[state=active]:text-blue-600 data-[state=active]:shadow-sm">General</TabsTrigger>
          <TabsTrigger value="funds" className="text-xs sm:text-sm data-[state=active]:bg-white data-[state=active]:text-blue-600 data-[state=active]:shadow-sm">Fund Config</TabsTrigger>
          <TabsTrigger value="members" className="text-xs sm:text-sm data-[state=active]:bg-white data-[state=active]:text-blue-600 data-[state=active]:shadow-sm">Members</TabsTrigger>
          <TabsTrigger value="valuation" className="text-xs sm:text-sm data-[state=active]:bg-white data-[state=active]:text-blue-600 data-[state=active]:shadow-sm">Valuation</TabsTrigger>
          {isAdmin && <TabsTrigger value="danger" className="text-xs sm:text-sm data-[state=active]:bg-destructive data-[state=active]:text-destructive-foreground data-[state=active]:shadow-sm">Danger Zone</TabsTrigger>}
        </TabsList>

        {/* Tab 1: General Club Information */}
        <TabsContent value="general" className="mt-6">
          <Card className="bg-white border-slate-200/75 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-medium text-slate-800">Club Details</CardTitle>
              <CardDescription className="text-sm text-slate-600">Update your club's name and public description.</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSaveClubDetails} className="space-y-6">
                <div>
                  <Label htmlFor="clubName" className="font-medium text-slate-700">Club Name</Label>
                  <Input id="clubName" value={clubName} onChange={(e) => setClubName(e.target.value)} required className="mt-1 border-slate-300 focus:border-blue-500 focus:ring-blue-500"/>
                </div>
                <div>
                  <Label htmlFor="clubDescription" className="font-medium text-slate-700">Club Description</Label>
                  <Textarea id="clubDescription" value={clubDescription} onChange={(e) => setClubDescription(e.target.value)} rows={4} className="mt-1 border-slate-300 focus:border-blue-500 focus:ring-blue-500"/>
                </div>
                <div className="flex justify-end">
                  <Button type="submit" className="bg-blue-600 hover:bg-blue-700" disabled={isUpdatingClub}>
                    {isUpdatingClub ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...
                      </>
                    ) : (
                      <>
                        <Save className="mr-2 h-4 w-4" /> Save Club Details
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 2: Fund Configuration */}
        <TabsContent value="funds" className="mt-6">
          <Card className="bg-white border-slate-200/75 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-medium text-slate-800">Fund Configuration</CardTitle>
              <CardDescription className="text-sm text-slate-600">Manage individual funds and how new cash is allocated.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <p className="text-sm text-slate-700">All fund settings, including creation, editing, and new cash allocation splits, are managed on the main "Club Funds" page.</p>
                <Button variant="outline" asChild className="bg-white border-slate-300 hover:bg-slate-50 text-blue-600 hover:text-blue-700">
                    <Link to={`/club/${clubId}/funds`}>
                        <Settings className="mr-2 h-4 w-4" /> Go to Club Funds Page <ExternalLink className="ml-1.5 h-3.5 w-3.5 opacity-70"/>
                    </Link>
                </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 3: Member Management */}
        <TabsContent value="members" className="mt-6">
          <Card className="bg-white border-slate-200/75 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-medium text-slate-800">Member Management</CardTitle>
              <CardDescription className="text-sm text-slate-600">Oversee club members, their roles, and invitations.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <p className="text-sm text-slate-700">Member invitations, role assignments, and viewing member equity are handled on the main "Club Members" page.</p>
                <Button variant="outline" asChild className="bg-white border-slate-300 hover:bg-slate-50 text-blue-600 hover:text-blue-700">
                    <Link to={`/club/${clubId}/members`}>
                        <Users className="mr-2 h-4 w-4" /> Go to Club Members Page <ExternalLink className="ml-1.5 h-3.5 w-3.5 opacity-70"/>
                    </Link>
                </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 4: Valuation Settings */}
        <TabsContent value="valuation" className="mt-6">
          <Card className="bg-white border-slate-200/75 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg font-medium text-slate-800">Valuation Settings</CardTitle>
              <CardDescription className="text-sm text-slate-600">Control how and when your club's unit value is calculated.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-md bg-slate-50 border border-slate-200/75">
                <h4 className="font-medium text-slate-700">Automatic Valuation</h4>
                <p className="text-xs text-slate-600 mt-1">Unit value is typically calculated automatically at the end of each defined period (e.g., daily or weekly) by the system.</p>
              </div>
              {isAdmin && (
                <div>
                  <h4 className="font-medium text-slate-700 mb-1">Manual Valuation Trigger</h4>
                  <p className="text-xs text-slate-600 mb-2">If needed (e.g., after significant market events or large member transactions intra-period), admins can trigger a manual recalculation.</p>
                  <Button 
                    variant="outline" 
                    onClick={handleTriggerManualValuation} 
                    className="bg-white border-slate-300 hover:bg-slate-50"
                    disabled={isCalculatingNav}
                  >
                    {isCalculatingNav ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Calculating...
                      </>
                    ) : (
                      <>
                        <BarChart2 className="mr-2 h-4 w-4 text-blue-600" /> Trigger Manual Unit Value Calculation
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab 5: Danger Zone (Admin only) */}
        {isAdmin && (
          <TabsContent value="danger" className="mt-6">
            <Card className="bg-white border-red-500/50 shadow-sm border-2">
              <CardHeader>
                <div className="flex items-center gap-2">
                    <AlertTriangle className="h-6 w-6 text-red-600" />
                    <CardTitle className="text-lg font-medium text-red-700">Danger Zone - Advanced Settings</CardTitle>
                </div>
                <CardDescription className="text-sm text-red-600/90">These actions can have significant consequences. Proceed with extreme caution.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Archive Club */} 
                <div>
                    <h4 className="font-semibold text-slate-800">Archive Club</h4>
                    <p className="text-sm text-slate-600 mt-1 mb-2">Archiving the club will make it read-only and hide it from public view. This action can usually be reversed by platform support. It does not delete data permanently.</p>
                    <Dialog open={showArchiveConfirmDialog} onOpenChange={setShowArchiveConfirmDialog}>
                        <DialogTrigger asChild>
                            <Button variant="destructive">
                                <Archive className="mr-2 h-4 w-4" /> Archive This Club
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-md bg-white">
                            <DialogHeader>
                                <DialogTitle className="text-red-700 flex items-center"><ShieldAlert className="mr-2 h-5 w-5"/>Confirm Club Archival</DialogTitle>
                                <DialogDescription className="mt-2">
                                    This action is significant. Archiving will make the club read-only.
                                    To confirm, please type "<strong className='text-red-700 font-bold'>archive {club.name}</strong>" in the box below.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="py-4 space-y-2">
                                <Label htmlFor="archiveConfirmText" className="text-slate-600">Confirmation Text:</Label>
                                <Input 
                                    id="archiveConfirmText" 
                                    value={archiveConfirmationText} 
                                    onChange={(e) => setArchiveConfirmationText(e.target.value)}
                                    placeholder={`archive ${club.name}`}
                                    className="border-red-300 focus:border-red-500 focus:ring-red-500"
                                />
                            </div>
                            <DialogFooter>
                                <DialogClose asChild><Button type="button" variant="outline">Cancel</Button></DialogClose>
                                <Button variant="destructive" onClick={handleArchiveClub} disabled={archiveConfirmationText !== `archive ${club.name}`}>
                                    <Archive className="mr-2 h-4 w-4"/> Confirm Archival
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>
                
                <hr className="border-slate-200"/>

                {/* Transfer Club Ownership */} 
                <div>
                    <h4 className="font-semibold text-slate-800">Transfer Club Ownership (Post-MVP)</h4>
                    <p className="text-sm text-slate-600 mt-1 mb-2">Transferring ownership to another admin member. This is an irreversible action for the current owner.</p>
                    <Button variant="outline" disabled className="border-slate-300">
                       Transfer Ownership (Feature Coming Soon)
                    </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
};

export default ClubSettingsPage;
