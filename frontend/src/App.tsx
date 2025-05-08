// src/App.tsx
import { Routes, Route } from 'react-router-dom'; // Removed useNavigate, useLocation
import { useAuth0 } from '@auth0/auth0-react';
// import { useEffect } from 'react'; // Removed useEffect

// No longer import LoginPage if you're removing the /login route entirely due to direct redirect
// import LoginPage from './pages/LoginPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { AuthNav } from './components/layout/AuthNav';
// import { User } from 'lucide-react';

// Import the actual UserLandingPage component instead of using a placeholder
import UserLandingPage from './pages/UserLandingPage';
const ClubDashboardPage = () => <div className="p-4"><h2 className="text-xl font-semibold">Club Dashboard</h2></div>;
const FundDetailPage = () => <div className="p-4"><h2 className="text-xl font-semibold">Fund Detail</h2></div>;
const PortfolioPage = () => <div className="p-4"><h2 className="text-xl font-semibold">Portfolio</h2></div>;
const BrokerageTransactionsPage = () => <div className="p-4"><h2 className="text-xl font-semibold">Brokerage Transactions</h2></div>;
const MembersPage = () => <div className="p-4"><h2 className="text-xl font-semibold">Members</h2></div>;
const ClubAccountingPage = () => <div className="p-4"><h2 className="text-xl font-semibold">Club Accounting</h2></div>;
const SettingsPage = () => <div className="p-4"><h2 className="text-xl font-semibold">Settings</h2></div>;
const NotFoundPage = () => <div className="p-4"><h2 className="text-xl font-semibold">404 - Page Not Found</h2></div>;

const MainLayout = ({ children }: { children: React.ReactNode }) => (
  <div>
    <header className="p-4 bg-gray-800 text-white flex justify-between items-center sticky top-0 z-50 shadow-md">
      <h1 className="text-xl font-bold">Social Investment Club</h1>
      <AuthNav />
    </header>
    {/* Ensure content doesn't hide under sticky header */}
    <main className="pt-16 md:pt-20">{/* Adjust padding-top based on header height */}
        <div className="container mx-auto px-4 py-6">
            {children}
        </div>
    </main>
  </div>
);

function App() {
  // Only isLoading is needed here from useAuth0 for the top-level loading gate
  const { isLoading } = useAuth0();

  // The useEffect for redirecting already authenticated users away from /login
  // is removed as ProtectedRoute now handles direct redirect to Auth0.
  // The onRedirectCallback in main.tsx handles where to go *after* Auth0 login.

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div>Initializing Application...</div>
        {/* You could use a shadcn Skeleton here for a better loading experience */}
      </div>
    );
  }

  return (
    <Routes>
      {/*
        If you decide to have a public landing page that *doesn't* require login immediately,
        it would go here, outside the ProtectedRoute. For example:
        <Route path="/landing" element={<PublicLandingPage />} />
        And then your ProtectedRoute might handle the root path '/' if no public landing page exists.
      */}

      {/* Protected Routes - these will trigger Auth0 login if not authenticated */}
      <Route element={<ProtectedRoute />}>
        {/* Default authenticated route could be club-selection */}
        <Route path="/" element={<MainLayout><UserLandingPage /></MainLayout>} />
        <Route path="/UserLandingPage" element={<MainLayout><UserLandingPage /></MainLayout>} />

        {/* Club-specific routes */}
        <Route path="/club/:clubId/dashboard" element={<MainLayout><ClubDashboardPage /></MainLayout>} />
        <Route path="/club/:clubId/funds/:fundId" element={<MainLayout><FundDetailPage /></MainLayout>} />
        <Route path="/club/:clubId/portfolio" element={<MainLayout><PortfolioPage /></MainLayout>} />
        <Route path="/club/:clubId/brokerage-transactions" element={<MainLayout><BrokerageTransactionsPage /></MainLayout>} />
        <Route path="/club/:clubId/members" element={<MainLayout><MembersPage /></MainLayout>} />
        <Route path="/club/:clubId/accounting" element={<MainLayout><ClubAccountingPage /></MainLayout>} />
        <Route path="/club/:clubId/settings" element={<MainLayout><SettingsPage /></MainLayout>} />
      </Route>

      {/*
        If you completely remove LoginPage.tsx, you won't have a /login route.
        If you want to keep it for some explicit linking or testing, you can add it outside ProtectedRoute:
        <Route path="/login-explicit" element={<OriginalLoginPageIfKept />} />
      */}

      <Route path="*" element={<MainLayout><NotFoundPage /></MainLayout>} /> {/* Catch-all for 404 */}
    </Routes>
  );
}

export default App;