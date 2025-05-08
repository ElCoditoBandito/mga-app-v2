// src/components/layout/AuthNav.tsx
import { useAuth0 } from "@auth0/auth0-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export const AuthNav = () => {
  const { logout, user, isAuthenticated, isLoading } = useAuth0();

  if (isLoading) {
    return <Skeleton className="h-8 w-32" />; // Adjusted width for typical "Hello, User | Logout"
  }

  if (!isAuthenticated) {
    // This component is typically used in layouts for authenticated users.
    // If it somehow renders when not authenticated, it shouldn't show anything or
    // could show a login button, but our ProtectedRoute handles unauthenticated access.
    return null;
  }

  return (
    <div className="flex items-center gap-4"> {/* Increased gap slightly */}
      <span className="text-sm font-medium"> {/* Added font-medium for better visibility */}
        {user?.name || user?.email || "Authenticated User"}
      </span>
      <Button
        variant="outline" // Or "ghost" or "default" as you prefer
        size="sm"
        onClick={() =>
          logout({ logoutParams: { returnTo: window.location.origin } })
        }
      >
        Log Out
      </Button>
    </div>
  );
};