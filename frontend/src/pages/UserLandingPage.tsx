// frontend/src/pages/UserLandingPage.tsx
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { PlusCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

// Import API hooks
import {
  useUserClubs,
  useCreateClub
} from '@/hooks/useApi';

// Helper functions
const formatValue = (value: unknown): string => {
  if (value == null) return 'N/A';
  if (typeof value === 'number') {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
  }
  return String(value);
};

const UserLandingPage = () => {
  const { user } = useAuth0();
  const [showCreateClubDialog, setShowCreateClubDialog] = useState(false);
  const [newClubName, setNewClubName] = useState('');
  const [newClubDescription, setNewClubDescription] = useState('');

  // Fetch user's clubs using React Query
  const { 
    data: clubs = [], 
    isLoading, 
    error 
  } = useUserClubs();

  // Mutation hook for creating a new club
  const { mutate: createClub, isPending: isCreatingClub } = useCreateClub();

  const handleCreateClub = () => {
    if (!newClubName.trim()) {
      toast.error('Club name is required');
      return;
    }

    createClub({
      name: newClubName.trim(),
      description: newClubDescription.trim() || undefined
    }, {
      onSuccess: () => {
        toast.success('Club created successfully');
        setShowCreateClubDialog(false);
        setNewClubName('');
        setNewClubDescription('');
      },
      onError: (error: unknown) => {
        console.error('Error creating club:', error);
        toast.error('Failed to create club');
      }
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">
            Welcome, {user?.name || user?.email || 'User'}!
          </h1>
          <p className="text-slate-600">Select a club to view its dashboard or manage your clubs.</p>
        </div>
        <Button 
          variant="outline" 
          className="bg-white"
          onClick={() => setShowCreateClubDialog(true)}
        >
          <PlusCircle className="mr-2 h-4 w-4" /> Create New Club
        </Button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-slate-600">Loading your clubs...</p>
          </div>
        </div>
      )}

      {error && (
        <Card className="bg-red-50 border-red-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-6 w-6 text-red-600" />
              <CardTitle className="text-red-700">Error Loading Clubs</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-red-600">Could not fetch your club information. Please try again later.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && clubs && clubs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 md:gap-6">
          {clubs.map((club) => (
            <Card
              key={club.id}
              className="bg-white border-slate-200/75 shadow-sm hover:shadow-md transition-all duration-200 ease-in-out flex flex-col"
            >
              <CardHeader>
                <CardTitle className="text-lg font-medium text-slate-800">{club.name}</CardTitle>
                <CardDescription className="text-xs text-slate-500 pt-0.5">
                  Your Role: <span className="font-semibold text-slate-600">
                    {club.current_user_role || 'Member'}
                  </span>
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-grow space-y-3">
                {club.description && (
                  <p className="text-sm text-slate-600 line-clamp-2">{club.description}</p>
                )}
                <div className="text-sm space-y-1 pt-1">
                  <p className="text-slate-500">
                    Members: <span className="font-medium text-slate-700">{club.memberships?.length || 0}</span>
                  </p>
                  {/* Club value would come from a separate API call in a real implementation */}
                  <p className="text-slate-500">
                    Club Value: <span className="font-medium text-slate-700">{formatValue('Coming soon')}</span>
                  </p>
                </div>
              </CardContent>
              <CardFooter>
                <Button asChild className="w-full bg-blue-600 hover:bg-blue-700 hover:-translate-y-px transform transition-all duration-150">
                  <Link to={`/club/${club.id}/dashboard`}>View Club</Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {!isLoading && !error && clubs && clubs.length === 0 && (
        <Card className="bg-white border-slate-200/75 shadow-sm">
          <CardHeader>
            <CardTitle className="text-slate-800">No Clubs Found</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-slate-600">You are not a member of any clubs yet.</p>
            <Button 
              variant="default" 
              className="mt-4 bg-blue-600 hover:bg-blue-700"
              onClick={() => setShowCreateClubDialog(true)}
            >
              <PlusCircle className="mr-2 h-4 w-4" /> Create Your First Club
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Create Club Dialog */}
      {showCreateClubDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold text-slate-800 mb-4">Create New Club</h2>
            <div className="space-y-4">
              <div>
                <Label htmlFor="clubName" className="font-medium text-slate-700">Club Name <span className="text-red-500">*</span></Label>
                <Input 
                  id="clubName" 
                  value={newClubName} 
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewClubName(e.target.value)}
                  placeholder="Enter club name" 
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="clubDescription" className="font-medium text-slate-700">Description (Optional)</Label>
                <Textarea 
                  id="clubDescription" 
                  value={newClubDescription} 
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setNewClubDescription(e.target.value)}
                  placeholder="Brief description of your club" 
                  rows={3} 
                  className="mt-1"
                />
              </div>
              <div className="flex justify-end space-x-3 pt-4">
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setShowCreateClubDialog(false)}
                  disabled={isCreatingClub}
                >
                  Cancel
                </Button>
                <Button 
                  type="button" 
                  className="bg-blue-600 hover:bg-blue-700" 
                  onClick={handleCreateClub}
                  disabled={isCreatingClub}
                >
                  {isCreatingClub ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Creating...
                    </>
                  ) : (
                    'Create Club'
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserLandingPage;
