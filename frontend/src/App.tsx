
// frontend/src/App.tsx
import { Routes, Route } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import ProtectedRoute from './components/auth/ProtectedRoute';
import { MainLayout } from './components/layout/MainLayout'; // Updated import
import { Skeleton } from '@/components/ui/skeleton'; // For loading state

// Import Page Components
// For now, using placeholders. Actual page components will be created later.
import UserLandingPage from './pages/UserLandingPage'; // Assuming this exists as per initial review

// Placeholder components for pages (replace with actual page components later)
// These will be developed according to the wireframes
import ClubDashboardPage from './pages/ClubDashboardPage';
import PortfolioPage from './pages/PortfolioPage';
import FundsPage from './pages/FundsPage';
import FundDetailPage from './pages/FundDetailPage';
import ClubAccountingPage from './pages/ClubAccountingPage';
import BrokerageLogPage from './pages/BrokerageLogPage';
import MembersPage from './pages/MembersPage';
import ClubSettingsPage from './pages/ClubSettingsPage';

// Using the NotFoundPage from wireframe specs, will create this page later
import NotFoundPage from './pages/NotFoundPage'; // Placeholder import, will create actual component

function App() {
  const { isLoading } = useAuth0();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-100">
        <div className="flex flex-col items-center space-y-4">
          <Skeleton className="h-12 w-12 rounded-full bg-slate-300" />
          <Skeleton className="h-4 w-48 bg-slate-300" />
          <Skeleton className="h-4 w-32 bg-slate-300" />
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route element={<ProtectedRoute />}>
        {/* Routes that use MainLayout (which includes Header and potentially Sidebar) */}
        <Route path="/" element={<MainLayout><UserLandingPage /></MainLayout>} />
        <Route path="/user-landing" element={<MainLayout><UserLandingPage /></MainLayout>} />

        {/* Club-specific routes now correctly use clubId in the path */}
        <Route path="/club/:clubId/dashboard" element={<MainLayout><ClubDashboardPage /></MainLayout>} />
        <Route path="/club/:clubId/portfolio" element={<MainLayout><PortfolioPage /></MainLayout>} />
        <Route path="/club/:clubId/funds" element={<MainLayout><FundsPage /></MainLayout>} />
        <Route path="/club/:clubId/funds/:fundId" element={<MainLayout><FundDetailPage /></MainLayout>} />
        <Route path="/club/:clubId/accounting" element={<MainLayout><ClubAccountingPage /></MainLayout>} />
        <Route path="/club/:clubId/brokerage-log" element={<MainLayout><BrokerageLogPage /></MainLayout>} />
        <Route path="/club/:clubId/members" element={<MainLayout><MembersPage /></MainLayout>} />
        <Route path="/club/:clubId/settings" element={<MainLayout><ClubSettingsPage /></MainLayout>} />
      </Route>

      {/* NotFoundPage can also use MainLayout or a simpler layout if preferred */}
      {/* For now, using MainLayout to maintain header consistency */}
      <Route path="*" element={<MainLayout><NotFoundPage /></MainLayout>} />
    </Routes>
  );
}

export default App;
