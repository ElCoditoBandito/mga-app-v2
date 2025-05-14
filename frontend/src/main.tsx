// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';
import { BrowserRouter } from 'react-router-dom';
import { Auth0ProviderWithNavigate } from './components/auth/Auth0ProviderWithNavigate';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Env var checks are now primarily within Auth0ProviderWithNavigate,
// but a top-level check here before rendering is still good practice.
const auth0Domain = import.meta.env.VITE_AUTH0_DOMAIN;
const auth0ClientId = import.meta.env.VITE_AUTH0_CLIENT_ID;
const auth0Audience = import.meta.env.VITE_AUTH0_AUDIENCE;

if (!auth0Domain || !auth0ClientId || !auth0Audience) {
  // Handle critical missing configuration early
  const rootElement = document.getElementById('root');
  if (rootElement) {
    ReactDOM.createRoot(rootElement).render(
      <React.StrictMode>
        <div className="p-5 text-center text-red-600 bg-red-50 min-h-screen flex flex-col justify-center items-center">
          <h1 className="text-2xl font-bold mb-3">Application Configuration Error</h1>
          <p className="mb-1">Auth0 environment variables (Domain, Client ID, or Audience) are not set.</p>
          <p>Please check your <code>.env</code> file and ensure it's loaded correctly.</p>
        </div>
      </React.StrictMode>
    );
  }
  throw new Error("Auth0 domain, client ID, or audience is not set in environment variables. App cannot start.");
}


const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Failed to find the root element. Please check your index.html file.");
}

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <Auth0ProviderWithNavigate>
        <QueryClientProvider client={queryClient}>
          <App />
        </QueryClientProvider>
      </Auth0ProviderWithNavigate>
    </BrowserRouter>
  </React.StrictMode>,
);