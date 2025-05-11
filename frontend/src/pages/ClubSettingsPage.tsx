
// frontend/src/pages/ClubSettingsPage.tsx
import React, { useState } from 'react';
import { useParams, Link, /*useNavigate*/ } from 'react-router-dom';
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
// import { Skeleton } from '@/components/ui/skeleton';
import { Settings, Users, BarChart2, AlertTriangle, Archive, ShieldAlert, Save, ExternalLink } from 'lucide-react';
// import { cn } from '@/lib/utils';

// --- Mock Data Structures ---
interface ClubSettingsData {
  clubId: string;
  clubName: string;
  clubDescription: string;
  isAdmin: boolean;
}

// --- Mock Data Generation ---
const MOCK_CLUB_SETTINGS_DATA: ClubSettingsData = {
  clubId: 'club123',
  clubName: 'Eagle Investors Club',
  clubDescription: 'A social investment club focused on long-term growth and member education. We primarily invest in US equities and ETFs.',
  isAdmin: true,
};

// --- Main Component ---
const ClubSettingsPage = () => {
  const { clubId } = useParams<{ clubId: string }>();
  // const navigate = useNavigate();

  const [pageData, setPageData] = useState<ClubSettingsData>(MOCK_CLUB_SETTINGS_DATA);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [isLoading, _setIsLoading] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [error, _setError] = useState<Error | null>(null);

  // Form state for General Club Information
  const [clubName, setClubName] = useState(pageData.clubName);
  const [clubDescription, setClubDescription] = useState(pageData.clubDescription);

  const [showArchiveConfirmDialog, setShowArchiveConfirmDialog] = useState(false);
  const [archiveConfirmationText, setArchiveConfirmationText] = useState('');

  const handleSaveClubDetails = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Saving club details:', { clubId, clubName, clubDescription });
    // API call to update club details
    // For mock, update local state:
    setPageData(prev => ({ ...prev, clubName, clubDescription }));
    alert('Club details saved (mock)!'); // Mock feedback
  };

  const handleTriggerManualValuation = () => {
    console.log('Triggering manual unit value calculation for club:', clubId);
    alert('Manual unit value calculation triggered (mock)!');
  };

  const handleArchiveClub = () => {
    if (archiveConfirmationText === `archive ${pageData.clubName}`) {
      console.log('Archiving club:', clubId);
      // API call to archive club
      setShowArchiveConfirmDialog(false);
      setArchiveConfirmationText('');
      alert(`Club '${pageData.clubName}' archived (mock)! You may be redirected.`);
      // Potentially navigate away, e.g., to user landing page
      // navigate('/'); 
    } else {
      alert('Confirmation text does not match. Please type the exact phrase to confirm.');
    }
  };

  if (isLoading) { /* Skeleton for loading state */ }
  if (error || !pageData) { /* Error state */ }

  const { isAdmin } = pageData;

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
                  <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                    <Save className="mr-2 h-4 w-4" /> Save Club Details
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
                  <Button variant="outline" onClick={handleTriggerManualValuation} className="bg-white border-slate-300 hover:bg-slate-50">
                    <BarChart2 className="mr-2 h-4 w-4 text-blue-600" /> Trigger Manual Unit Value Calculation
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
                                    To confirm, please type "<strong className='text-red-700 font-bold'>archive {pageData.clubName}</strong>" in the box below.
                                </DialogDescription>
                            </DialogHeader>
                            <div className="py-4 space-y-2">
                                <Label htmlFor="archiveConfirmText" className="text-slate-600">Confirmation Text:</Label>
                                <Input 
                                    id="archiveConfirmText" 
                                    value={archiveConfirmationText} 
                                    onChange={(e) => setArchiveConfirmationText(e.target.value)}
                                    placeholder={`archive ${pageData.clubName}`}
                                    className="border-red-300 focus:border-red-500 focus:ring-red-500"
                                />
                            </div>
                            <DialogFooter>
                                <DialogClose asChild><Button type="button" variant="outline">Cancel</Button></DialogClose>
                                <Button variant="destructive" onClick={handleArchiveClub} disabled={archiveConfirmationText !== `archive ${pageData.clubName}`}>
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
