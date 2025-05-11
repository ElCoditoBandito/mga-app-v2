// frontend/src/components/layout/Header.tsx
import { Link } from 'react-router-dom';
import { AuthNav } from './AuthNav';
import { Button } from '@/components/ui/button';
import { Menu } from 'lucide-react';

// Placeholder for ClubSwitcher - to be implemented later
const ClubSwitcherPlaceholder = () => (
  <div className="text-sm text-slate-300 hover:text-white transition-colors">
    {/* Replace with actual ClubSwitcher Dropdown from shadcn/ui later */}
    <span>Current Club Name / Select Club</span>
  </div>
);

interface HeaderProps {
  onToggleSidebar: () => void;
}

export const Header = ({ onToggleSidebar }: HeaderProps) => {
  return (
    <header className="bg-slate-900 text-white shadow-md fixed top-0 left-0 right-0 z-50 h-16 flex items-center px-4 md:px-6">
      <div className="flex items-center w-full">
        {/* Mobile Sidebar Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleSidebar}
          className="md:hidden mr-2 text-slate-300 hover:text-white hover:bg-slate-800"
          aria-label="Toggle sidebar"
        >
          <Menu className="h-6 w-6" />
        </Button>

        {/* App Logo/Name */}
        <Link to="/" className="text-xl font-bold text-white hover:text-slate-200 transition-colors">
          Social Investment Hub
        </Link>

        <div className="flex-grow"></div> {/* Spacer */}

        {/* Right Section */}
        <div className="flex items-center space-x-4">
          <ClubSwitcherPlaceholder />
          <AuthNav />
        </div>
      </div>
    </header>
  );
};
