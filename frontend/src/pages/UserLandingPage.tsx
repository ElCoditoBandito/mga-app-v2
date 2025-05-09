
// frontend/src/pages/UserLandingPage.tsx
import { Link } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { PlusCircle } from 'lucide-react';

// Mock data - replace with API call
// Assuming a structure like:
// interface ClubMembership { club: { id: string; name: string; description?: string; }; role: string; }
// interface UserProfile { clubs: ClubMembership[]; }
const MOCK_USER_CLUBS_DATA = {
  isLoading: false,
  error: null,
  data: [
    {
      club: {
        id: 'club123',
        name: 'Eagle Investors Club',
        description: 'Focused on long-term value investments in the tech sector.',
        totalMembers: 12,
        clubValue: 125034.78,
      },
      role: 'Admin',
    },
    {
      club: {
        id: 'club456',
        name: 'Mountain View Capital',
        description: 'Aggressive growth strategies with a mix of equities and options.',
        totalMembers: 8,
        clubValue: 78345.90,
      },
      role: 'Member',
    },
    {
      club: {
        id: 'club789',
        name: 'Sunset Ventures',
        description: 'Early-stage startup investments and angel funding.',
        totalMembers: 23,
        // clubValue: null, // Example of missing value
      },
      role: 'Member',
    },
  ],
};

// Helper to format currency
const formatCurrency = (value?: number | null) => {
  if (value == null) return 'N/A';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
};

const UserLandingPage = () => {
  const { user } = useAuth0();
  // const { data: clubs, isLoading, error } = useQuery('userClubs', fetchUserClubs); // Replace with actual data fetching

  // Using mock data for now
  const { data: clubs, isLoading, error } = MOCK_USER_CLUBS_DATA;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">
            Welcome, {user?.name || user?.email || 'User'}!
          </h1>
          <p className="text-slate-600">Select a club to view its dashboard or manage your clubs.</p>
        </div>
        <Button variant="outline" className="bg-white">
          <PlusCircle className="mr-2 h-4 w-4" /> Create New Club
        </Button>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="bg-white border-slate-200/75 shadow-sm">
              <CardHeader>
                <Skeleton className="h-6 w-3/4 bg-slate-200" />
                <Skeleton className="h-4 w-1/2 bg-slate-200 mt-1" />
              </CardHeader>
              <CardContent className="space-y-2">
                <Skeleton className="h-4 w-full bg-slate-200" />
                <Skeleton className="h-4 w-5/6 bg-slate-200" />
                <Skeleton className="h-4 w-1/3 bg-slate-200 mt-2" />
                <Skeleton className="h-4 w-1/2 bg-slate-200" />
              </CardContent>
              <CardFooter>
                <Skeleton className="h-10 w-full bg-slate-200" />
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {error && (
        <Card className="bg-red-50 border-red-200">
          <CardHeader>
            <CardTitle className="text-red-700">Error Loading Clubs</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-red-600">Could not fetch your club information. Please try again later.</p>
            {/* <p className="text-xs text-red-500 mt-1">{error.message}</p> */}
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && clubs && clubs.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 md:gap-6">
          {clubs.map(({ club, role }) => (
            <Card
              key={club.id}
              className="bg-white border-slate-200/75 shadow-sm hover:shadow-md transition-all duration-200 ease-in-out flex flex-col"
            >
              <CardHeader>
                <CardTitle className="text-lg font-medium text-slate-800">{club.name}</CardTitle>
                <CardDescription className="text-xs text-slate-500 pt-0.5">
                  Your Role: <span className="font-semibold text-slate-600">{role}</span>
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-grow space-y-3">
                {club.description && (
                  <p className="text-sm text-slate-600 line-clamp-2">{club.description}</p>
                )}
                <div className="text-sm space-y-1 pt-1">
                  {club.totalMembers !== undefined && (
                    <p className="text-slate-500">
                      Members: <span className="font-medium text-slate-700">{club.totalMembers}</span>
                    </p>
                  )}
                  {club.clubValue !== undefined && (
                     <p className="text-slate-500">
                      Club Value: <span className="font-medium text-slate-700">{formatCurrency(club.clubValue)}</span>
                    </p>
                  )}
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
            <Button variant="default" className="mt-4 bg-blue-600 hover:bg-blue-700">
              <PlusCircle className="mr-2 h-4 w-4" /> Create Your First Club
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default UserLandingPage;
