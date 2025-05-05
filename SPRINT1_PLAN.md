# Sprint 1 Plan: Core Backend API & Security Setup

**Goal:** Establish a solid backend foundation by implementing the core API structure, securing endpoints with Auth0 JWT validation, and creating CRUD operations for Users, Clubs, and Memberships.

**Key Decisions & Assumptions:**

*   **Authentication:** Auth0 handles user signup/login. The backend verifies JWTs.
*   **User Sync:** The frontend will trigger a `POST /users` call after a successful Auth0 login if the user doesn't exist in the local database, syncing essential details (`auth0_id`, `email`, `name`).
*   **Authorization:** Initial rules are defined: Club Owners can delete clubs; Owners/Admins can manage memberships.
*   **Database:** PostgreSQL is set up, connection strings are configured, and initial migrations are assumed functional.
*   **MVP Focus:** Initial club creation is manual via the API; the creator becomes the owner. Invite flows are deferred.

**Refined Tasks for Sprint 1:**

1.  **Task 1.1 (Refined): Backend Structure Setup**
    *   **Action:** Create the necessary directory structure and initial Python files within the `backend/` directory:
        *   `api/` (for endpoint routers: `users.py`, `clubs.py`, `memberships.py`)
        *   `schemas/` (for Pydantic models: `user.py`, `club.py`, `membership.py`)
        *   `crud/` (for database operations: `user.py`, `club.py`, `membership.py`)
        *   `dependencies/` (for shared dependencies: `auth.py`, `database.py`)
        *   `tests/` (for unit tests: `test_users.py`, `test_clubs.py`, `test_memberships.py`)
    *   **Action:** Update `backend/main.py` to include the API routers from `backend/api/`.
    *   **Action:** Implement the database session dependency in `backend/dependencies/database.py`.

2.  **Task 1.2 (Refined): Auth0 JWT Verification**
    *   **Prerequisite:** Configure the Auth0 API Audience.
        *   **Guidance:** In your Auth0 Dashboard -> Applications -> APIs, create an API for this backend (e.g., "MGA Wealth API"). The "Identifier" you set for this API is your **Audience**. Use this value for `AUTH0_AUDIENCE` in `backend/.env`. Ensure the frontend Auth0Provider requests this audience.
    *   **Action:** Add `AUTH0_DOMAIN` and the obtained `AUTH0_AUDIENCE` to `backend/.env`.
    *   **Action:** Implement the JWT verification logic in `backend/dependencies/auth.py`. This should include fetching JWKS, decoding the token, and verifying the audience and issuer. Create a reusable FastAPI dependency (e.g., `get_current_active_user`) that performs verification and returns user information (like `auth0_id`) from the token.

3.  **Task 1.3 (Refined): User Endpoints & Sync**
    *   **Action:** Define Pydantic schemas in `backend/schemas/user.py` (`UserRead`, `UserCreate` - based on token info).
    *   **Action:** Implement CRUD functions in `backend/crud/user.py` (`get_user_by_auth0_id`, `create_user`).
    *   **Action:** Implement API routes in `backend/api/users.py`:
        *   `POST /users`: (Protected) Uses `get_current_active_user`. Checks if user exists via `auth0_id`. If not, calls `crud.create_user` using info from the token. Returns the user record.
        *   `GET /users/me`: (Protected) Uses `get_current_active_user`. Retrieves and returns the current user's details from the local database.

4.  **Task 1.4 (Refined): Club Endpoints**
    *   **Action:** Define Pydantic schemas in `backend/schemas/club.py` (`ClubRead`, `ClubCreate`, `ClubUpdate`).
    *   **Action:** Implement CRUD functions in `backend/crud/club.py`. `create_club` must also create an associated 'Owner' `Membership` record for the creator.
    *   **Action:** Implement API routes in `backend/api/clubs.py`:
        *   `POST /clubs`: (Protected) Creates a club, sets creator as Owner.
        *   `GET /clubs`: (Protected) Lists clubs.
        *   `GET /clubs/{club_id}`: (Protected) Gets club details (requires membership).
        *   `PUT /clubs/{club_id}`: (Protected) Updates club (requires Owner role).
        *   `DELETE /clubs/{club_id}`: (Protected) Deletes club (requires Owner role). Implement role checks using dependencies.

5.  **Task 1.5 (Refined): Membership Endpoints**
    *   **Action:** Define Pydantic schemas in `backend/schemas/membership.py` (`MembershipRead`, `MembershipCreate`, `MembershipUpdate`).
    *   **Action:** Implement CRUD functions in `backend/crud/membership.py`.
    *   **Action:** Implement API routes in `backend/api/memberships.py`:
        *   `POST /clubs/{club_id}/memberships`: (Protected) Adds a user to a club (requires Owner/Admin role).
        *   `GET /clubs/{club_id}/memberships`: (Protected) Lists members (requires membership).
        *   `PUT /memberships/{membership_id}`: (Protected) Updates role (requires Owner/Admin role).
        *   `DELETE /memberships/{membership_id}`: (Protected) Removes member (requires Owner/Admin role). Implement role checks using dependencies.

6.  **Task 1.6: Unit Testing**
    *   **Action:** Set up `pytest` and necessary plugins (e.g., `pytest-asyncio`).
    *   **Action:** Write unit tests in `backend/tests/` for CRUD functions and API endpoints, mocking database sessions and authentication dependencies. Verify responses, status codes, and authorization logic.

7.  **Task 1.7: API Documentation**
    *   **Action:** Ensure FastAPI automatically generates comprehensive Swagger UI documentation from Pydantic models and route definitions. Add descriptions where needed.

**High-Level Flow Diagram:**

```mermaid
graph TD
    subgraph Frontend (React/Auth0 SDK)
        direction LR
        A[User Login/Signup via Auth0] --> B(Get Auth0 ID Token);
        B --> C{User in Local DB?};
        C -- No --> D[Call POST /users API];
        C -- Yes --> E[Authenticated Session];
        E --> F[Call Club/Membership APIs];
    end

    subgraph Backend (FastAPI)
        direction LR
        G[API Request w/ Token] --> H(Auth Dependency);
        H -- Valid Token --> I[Get User Info (auth0_id)];
        H -- Invalid Token --> J[401/403 Error];
        I --> K{User Exists?};
        K -- No & POST /users --> L[CRUD: Create User];
        K -- Yes / Other Routes --> M[Proceed to Route Logic];
        M --> N[Club/Membership CRUD];
        N --> O[Role Check Dependency];
        O -- Authorized --> P[Execute DB Action];
        O -- Unauthorized --> J;
        L --> Q[User Table];
        P --> R[Club/Membership Tables];
    end

    subgraph Database (PostgreSQL)
        Q; R;
    end

    D --> G;
    F --> G;
    H -.->|Verify Audience/Issuer| S(Auth0 JWKS Endpoint);