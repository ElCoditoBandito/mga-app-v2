
// frontend/src/components/layout/MainLayout.tsx
import React, { useState, useEffect } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { cn } from '@/lib/utils';

// Placeholder for actual club data fetching
// In a real app, this would come from a global state/context or API call
const MOCK_CLUBS_DATA = {
  'club123': { id: 'club123', name: 'Eagle Investors Club' },
  'club456': { id: 'club456', name: 'Mountain View Capital' },
};

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout = ({ children }: MainLayoutProps) => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const location = useLocation();
  const { clubId } = useParams<{ clubId?: string }>();

  const currentClub = clubId ? MOCK_CLUBS_DATA[clubId as keyof typeof MOCK_CLUBS_DATA] : undefined;
  const clubName = currentClub?.name || (clubId ? 'Selected Club' : 'No Club Selected');

  const toggleSidebarCollapse = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  const toggleMobileSidebar = () => {
    setIsMobileSidebarOpen(!isMobileSidebarOpen);
  };

  const closeMobileSidebar = () => {
    setIsMobileSidebarOpen(false);
  };

  // Close mobile sidebar on route change
  useEffect(() => {
    closeMobileSidebar();
  }, [location.pathname]);

  // Determine if the sidebar should be shown based on the route
  // For MVP, sidebar is shown if there's a clubId in the path.
  const showSidebar = !!clubId;

  return (
    <div className="flex flex-col min-h-screen bg-slate-100">
      <Header onToggleSidebar={toggleMobileSidebar} />

      <div className="flex flex-1 pt-16"> {/* Adjust pt to match header height */}
        {showSidebar && (
          <Sidebar
            clubName={clubName}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={toggleSidebarCollapse}
            isMobileOpen={isMobileSidebarOpen}
            onCloseMobile={closeMobileSidebar}
          />
        )}

        <main
          className={cn(
            'flex-1 transition-all duration-300 ease-in-out',
            showSidebar && 'md:ml-64', // Default sidebar width
            showSidebar && isSidebarCollapsed && 'md:ml-20' // Collapsed sidebar width
          )}
        >
          <div className="container mx-auto px-4 py-6 md:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};
