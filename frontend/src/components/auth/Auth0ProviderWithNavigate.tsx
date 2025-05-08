// src/auth/Auth0ProviderWithNavigate.tsx
import React from 'react';
import { Auth0Provider } from '@auth0/auth0-react';
import type { AppState } from '@auth0/auth0-react';
import { useNavigate } from 'react-router-dom';

// Retrieve Auth0 configuration from environment variables
// These need to be accessible here, or passed as props if you prefer
const auth0Domain = import.meta.env.VITE_AUTH0_DOMAIN;
const auth0ClientId = import.meta.env.VITE_AUTH0_CLIENT_ID;
const auth0Audience = import.meta.env.VITE_AUTH0_AUDIENCE;

if (!auth0Domain || !auth0ClientId || !auth0Audience) {
  // This check is duplicated, but good for component self-sufficiency
  // Or, ensure main.tsx only renders this if vars are present.
  console.error("Auth0 environment variables not fully configured for Auth0ProviderWithNavigate.");
  // Decide on error handling: throw, or return a fallback UI.
  // For now, let it proceed, main.tsx has the primary check.
}

interface Auth0ProviderWithNavigateProps {
  children: React.ReactNode;
}

export const Auth0ProviderWithNavigate: React.FC<Auth0ProviderWithNavigateProps> = ({ children }) => {
  const navigate = useNavigate();

  const onRedirectCallback = (appState?: AppState) => {
    const targetPath = appState?.returnTo || '/UserLandingPage';
    console.log(`Auth0ProviderWithNavigate onRedirectCallback: Navigating to ${targetPath}`);
    navigate(targetPath, { replace: true });
  };

  // Ensure domain and clientId are valid before rendering Auth0Provider
  if (!auth0Domain || !auth0ClientId) {
    // This case should ideally be caught earlier by the checks in main.tsx before this component is rendered.
    // If it still happens, rendering an error message or null might be appropriate.
    return <div>Error: Auth0 Domain or Client ID is missing.</div>;
  }

  return (
    <Auth0Provider
      domain={auth0Domain}
      clientId={auth0ClientId}
      authorizationParams={{
        redirect_uri: window.location.origin,
        audience: auth0Audience,
      }}
      onRedirectCallback={onRedirectCallback}
      // cacheLocation="localstorage" // Good for persisting session
    >
      {children}
    </Auth0Provider>
  );
};