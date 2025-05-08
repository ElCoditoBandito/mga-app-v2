// src/components/auth/ProtectedRoute.tsx
import React, { useEffect } from 'react'; // Added useEffect
// Removed Navigate and Outlet as we might handle this differently for direct redirect
// import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { Outlet, useLocation } from 'react-router-dom'; // Keep Outlet and useLocation

const WHITELIST_ORGANIZATION_ID = import.meta.env.VITE_AUTH0_WHITELIST_ORG_ID;

if (!WHITELIST_ORGANIZATION_ID) {
  console.error("CRITICAL: VITE_AUTH0_WHITELIST_ORG_ID is not defined in environment variables! Cannot specify organization for login.");
  // Consider how to handle this - maybe return an error display component?
  // For now, logging the error might suffice, but the login redirect might fail or have unintended consequences.
}

const ProtectedRoute: React.FC = () => {
  const { isAuthenticated, isLoading, loginWithRedirect } = useAuth0();
  const location = useLocation();

  useEffect(() => {
    // Only attempt to redirect if not loading and not authenticated
    if (!isLoading && !isAuthenticated) {
      console.log("ProtectedRoute: User not authenticated, redirecting to Auth0 login...");
      if (WHITELIST_ORGANIZATION_ID) { // Only add org context if ID is available
        loginWithRedirect({
          appState: { returnTo: location.pathname + location.search + location.hash }, // Send the full intended path
          authorizationParams: {
            organization: WHITELIST_ORGANIZATION_ID
          }
        });
      } else {
        // Fallback or handle error if Org ID is missing - depends on requirements
        console.error("Cannot redirect to login: Whitelist Organization ID is missing.");
        // Potentially set an error state to display to the user
        loginWithRedirect({
          appState: { returnTo: location.pathname + location.search + location.hash }, // Send the full intended path
        });
      }
    }
  }, [isLoading, isAuthenticated, loginWithRedirect, location]);


  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div>Loading authentication status...</div>
      </div>
    );
  }

  // If authenticated, render the child routes.
  // If not authenticated, the useEffect above will have triggered a redirect,
  // so this part ideally isn't reached or is quickly navigated away from.
  // You could also return null here while redirect is in progress, though useEffect handles it.
  return isAuthenticated ? <Outlet /> : null; // Or a minimal loading/redirecting spinner
};

export default ProtectedRoute;