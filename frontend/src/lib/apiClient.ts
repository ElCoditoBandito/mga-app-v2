// src/lib/apiClient.ts
import type { Auth0ContextInterface } from "@auth0/auth0-react"; // Import the type


// Define a type for the getAccessTokenSilently function
type GetAccessTokenSilentlyType = Auth0ContextInterface['getAccessTokenSilently'];

// Function to create an authenticated fetch wrapper
export const createApiClient = (getAccessTokenSilently: GetAccessTokenSilentlyType) => {
  const baseURL = import.meta.env.VITE_API_URL;

  if (!baseURL) {
    throw new Error("VITE_API_URL is not defined in environment variables.");
  }

  return async (endpoint: string, options: RequestInit = {}): Promise<Response> => {
    console.log(`API Client: Preparing request to ${endpoint}`);
    let token: string | undefined;
    try {
      console.log(`API Client: Getting access token for audience: ${import.meta.env.VITE_AUTH0_AUDIENCE}`);
      token = await getAccessTokenSilently({
        authorizationParams: {
          audience: import.meta.env.VITE_AUTH0_AUDIENCE,
        },
      });
      console.log(`API Client: Successfully obtained access token`);
    } catch (error) {
      console.error("Error getting access token:", error);
      // Handle token error appropriately - maybe trigger login?
      // For now, just throw to indicate failure
      throw new Error("Failed to get authentication token.");
    }

    const headers = new Headers(options.headers);
    headers.set('Authorization', `Bearer ${token}`);
    // Add content-type header if sending JSON data
    if (options.body && typeof options.body === 'string' && (!options.headers || !('Content-Type' in options.headers))) {
         try {
             JSON.parse(options.body); // Check if it's valid JSON
             headers.set('Content-Type', 'application/json');
         } catch (e) {
             console.log(e);
         }
     }


    const config: RequestInit = {
      ...options,
      headers,
    };

    const url = `${baseURL}${endpoint}`; // Ensure endpoint starts with '/'
    console.log(`API Call: ${options.method || 'GET'} ${url}`); // Log the call
    console.log(`API Call Headers: Authorization: Bearer ${token ? 'token-exists' : 'no-token'}`);

    try {
      console.log(`API Client: Sending fetch request to ${url}`);
      const response = await fetch(url, config);
      console.log(`API Client: Received response with status: ${response.status}`);
      
      if (!response.ok) {
        // Attempt to read error details from response body
        let errorDetail = `HTTP error! status: ${response.status}`;
        try {
          const errorData = await response.json();
          errorDetail = errorData.detail || JSON.stringify(errorData);
        } catch (e) {
          console.log(e);
        }
        console.error(`API Error: ${options.method || 'GET'} ${url} - Status ${response.status} - ${errorDetail}`);
        // Throw an error that includes details if possible
        class ApiError extends Error {
          status: number;
          response: Response;

          constructor(message: string, status: number, response: Response) {
            super(message);
            this.status = status;
            this.response = response;
          }
        }

        const error = new ApiError(errorDetail, response.status, response);
        throw error;
      }
      
      return response; // Return the raw response for the caller to handle .json(), .text() etc.
    } catch (error) {
      console.error(`API Client: Fetch error for ${url}:`, error);
      throw error;
    }
  };
};

// Type for the returned API client function
export type ApiClient = ReturnType<typeof createApiClient>;