
// frontend/src/components/layout/Sidebar.tsx
import { NavLink, useParams } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  LayoutDashboard,
  PieChart,
  Users,
  Settings,
  Landmark,
  ListChecks,
  ArrowLeftRight,
  ChevronsLeft,
  ChevronsRight,
} from 'lucide-react';

interface SidebarProps {
  clubName?: string;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
}

const navLinkClasses = (
  isActive: boolean,
  isCollapsed: boolean
) => cn(
  'flex items-center px-3 py-2.5 text-sm font-medium transition-colors duration-150 ease-in-out',
  'hover:bg-slate-700 hover:text-white rounded-md',
  isActive ? 'bg-blue-600 text-white' : 'text-slate-300',
  isCollapsed ? 'justify-center' : 'justify-start'
);

const navIconClasses = (isCollapsed: boolean) => cn('h-5 w-5', isCollapsed ? '' : 'mr-3');
const navTextClasses = (isCollapsed: boolean) => cn(isCollapsed ? 'sr-only' : 'block');

const clubNavItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/portfolio', icon: PieChart, label: 'Portfolio' },
  { to: '/funds', icon: ListChecks, label: 'Funds' },
  { to: '/accounting', icon: Landmark, label: 'Club Accounting' },
  { to: '/brokerage-log', icon: ArrowLeftRight, label: 'Brokerage Log' },
  { to: '/members', icon: Users, label: 'Members' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export const Sidebar = ({
  clubName = 'No Club Selected',
  isCollapsed,
  onToggleCollapse,
  isMobileOpen,
  onCloseMobile
}: SidebarProps) => {
  const { clubId } = useParams<{ clubId?: string }>();

  const baseClubPath = clubId ? `/club/${clubId}` : '';

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Club Name / Top Section */}
      <div className={cn(
        'h-16 flex items-center border-b border-slate-700 px-4',
        isCollapsed ? 'justify-center' : 'justify-between'
      )}>
        <h2 className={cn(
          'text-lg font-semibold text-white whitespace-nowrap overflow-hidden text-ellipsis',
          isCollapsed ? 'sr-only' : 'block'
        )}>
          {clubName}
        </h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCollapse}
          className="hidden md:flex text-slate-400 hover:text-white hover:bg-slate-700"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <ChevronsRight className="h-5 w-5" /> : <ChevronsLeft className="h-5 w-5" />}
        </Button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-grow p-3 space-y-1.5 overflow-y-auto">
        {clubId ? (
          clubNavItems.map((item) => (
            <NavLink
              key={item.to}
              to={`${baseClubPath}${item.to}`}
              className={({ isActive }) => navLinkClasses(isActive, isCollapsed)}
              onClick={onCloseMobile} // Close mobile sidebar on link click
            >
              <item.icon className={navIconClasses(isCollapsed)} aria-hidden="true" />
              <span className={navTextClasses(isCollapsed)}>{item.label}</span>
            </NavLink>
          ))
        ) : (
          <div className={cn(
            'text-slate-400 text-sm px-3 py-2',
            isCollapsed ? 'text-center' : ''
          )}>
            {isCollapsed ? <ChevronsRight className="h-5 w-5 mx-auto" /> : 'Select a club to see navigation.'}
          </div>
        )}
      </nav>

      {/* Footer or other items can go here */}
    </div>
  );

  return (
    <>
      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          aria-hidden="true"
        />
      )}

      {/* Desktop Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-40 h-screen bg-slate-800 text-white transition-all duration-300 ease-in-out',
          'hidden md:block',
          isCollapsed ? 'w-20' : 'w-64'
        )}
      >
        {sidebarContent}
      </aside>

      {/* Mobile Drawer */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-40 h-screen bg-slate-800 text-white transition-transform duration-300 ease-in-out md:hidden',
          'w-64', // Mobile sidebar is always full width when open
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {sidebarContent}
      </aside>
    </>
  );
};
