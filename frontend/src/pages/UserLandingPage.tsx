// src/pages/ClubSelectionPage.tsx
import { useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { createApiClient,  type ApiClient } from '@/lib/apiClient'; // Import the utility

// Define a type for the user data we expect from /users/me
interface UserProfile {
  id: string;
  email: string;
  auth0_sub: string;
  is_active: boolean;
  // Add other fields if your UserRead schema includes them
}

const UserLandingPage = () => {
  const { getAccessTokenSilently, user: auth0User } = useAuth0(); // Get token function and basic user info
  const [backendUser, setBackendUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [apiClient, setApiClient] = useState<ApiClient | null>(null);

  // Create the API client instance once getAccessTokenSilently is available
  useEffect(() => {
    if (getAccessTokenSilently) {
      setApiClient(() => createApiClient(getAccessTokenSilently)); // Pass the function correctly
    }
  }, [getAccessTokenSilently]);

  // Fetch user data from backend when the component mounts and apiClient is ready
  useEffect(() => {
    const fetchUserData = async () => {
      if (!apiClient) {
        console.log("UserLandingPage: apiClient not ready yet.");
        return; // Don't fetch if apiClient isn't initialized
      }

      setIsLoading(true);
      setError(null);
      console.log("UserLandingPage: Attempting to fetch /users/me"); // Log fetch attempt

      try {
        const response = await apiClient('/users/me'); // Call the /users/me endpoint
        const userData: UserProfile = await response.json();
        setBackendUser(userData);
        console.log("UserLandingPage: Successfully fetched backend user data:", userData);
      } catch (err) {
        let message = "Failed to fetch user data from backend.";
        if (err instanceof Error) {
          message = err.message;
        } else if (typeof err === 'string') { // Changed 'error' to 'err' to avoid confusion with state variable
          message = err;
        }
        setError(message);
        console.error(message, err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserData();
  }, [apiClient]); // Only re-run when apiClient changes to avoid dependency cycles
// Function to manually trigger the API call for testing
const handleManualFetch = async () => {
  if (!apiClient) {
    console.log("API client not ready yet");
    return;
  }
  
  setIsLoading(true);
  setError(null);
  console.log("Manual fetch: Attempting to fetch /users/me");
  
  try {
    const response = await apiClient('/users/me');
    const userData: UserProfile = await response.json();
    setBackendUser(userData);
    console.log("Manual fetch: Successfully fetched backend user data:", userData);
  } catch (err) {
    let message = "Failed to fetch user data from backend.";
    if (err instanceof Error) {
      message = err.message;
    } else if (typeof err === 'string') { // Added to match the pattern in the useEffect
      message = err;
    }
    setError(message);
    console.error(message, err);
  } finally {
    setIsLoading(false);
  }
};

return (
  <div>
    <h2 className="text-2xl font-semibold mb-4">Club Selection</h2>

    {isLoading && <p>Loading user information...</p>}
    {error && <p className="text-red-500">Error: {error}</p>}
    
    <button
      onClick={handleManualFetch}
      className="mb-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
    >
      Test API Connection
    </button>


      {backendUser ? (
        <div>
          <p>Welcome, {backendUser.email}!</p>
          <p>(Backend User ID: {backendUser.id})</p>
          <p>Select a club to continue.</p>
          {/* TODO: Add logic to fetch and display clubs */}
        </div>
      ) : (
        !isLoading && !error && <p>Waiting for user data...</p>
      )}

      {/* Display basic Auth0 info for debugging if needed */}
      <pre className="mt-4 p-2 bg-gray-100 text-xs overflow-auto">
        Auth0 User Info: {JSON.stringify(auth0User, null, 2)}
      </pre>
    </div>
  );
};

export default UserLandingPage;