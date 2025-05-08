// src/pages/LoginPage.tsx
import { LoginForm } from "@/components/auth/LoginForm"; // Import the LoginForm component
import { useAuth0 } from "@auth0/auth0-react";
import { Navigate } from "react-router-dom"; // We'll use this after setting up routing

export default function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth0();

  // If Auth0 is still loading session information, show a generic loading state
  // This prevents a flash of the login form if the user is already authenticated
  // and being redirected.
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        Loading session...
      </div>
    );
  }

  // If user is already authenticated, redirect them from the login page
  // (e.g., to club selection or dashboard). We'll implement this with React Router.
  // For now, this logic shows the concept.
  if (isAuthenticated) {
    return <Navigate to="/club-selection" replace />;
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-100 p-4 dark:bg-gray-900">
      <LoginForm /> {/* Use the LoginForm component here */}
      {/* You can add other page-specific elements here if needed,
          like links to terms or a global footer, though the block
          might already handle some of these if you use more of its structure.
      */}
       {/* Example from one of the blocks if you want to include it at page level:
      <div className="mt-4 text-center text-sm text-muted-foreground">
        Access your club's investment dashboard.
      </div>
      */}
    </div>
  );
}