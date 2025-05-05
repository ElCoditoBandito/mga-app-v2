# Project Testing Strategy

This document outlines the testing strategy for the Investment Club Management Platform.

## Overall Goals

*   Ensure code quality, correctness, and reliability.
*   Prevent regressions during development.
*   Validate application behavior against requirements.
*   Provide confidence in deployments.

## Backend Testing (Python/FastAPI)

### Framework
*   **pytest:** The primary framework for running backend tests.
*   **pytest fixtures:** Used extensively for setting up test preconditions (database connections, authentication, test data).

### Database Strategy
*   **Engine:** Tests will run against a **PostgreSQL** database to ensure high fidelity with the production environment.
*   **Isolation:** Each test run will use a dedicated, temporary test database (e.g., `mga_test_db`) created and destroyed by the test suite setup/teardown (`conftest.py::db_engine` fixture). This ensures test isolation and repeatability.
*   **Schema Management:** The test database schema will be created using `SQLAlchemy Base.metadata.create_all()` at the start of each test session.
*   **Data Seeding:** Specific test data required for certain scenarios (e.g., predefined users, clubs) will be seeded using dedicated pytest fixtures (e.g., `seed_test_user`).

### Test Types
*   **Unit Tests:** Focus on testing individual functions and classes in isolation (e.g., CRUD operations, utility functions). Mocking external dependencies (like database sessions or external APIs) is common here. Located in `backend/tests/`.
*   **Integration Tests (API Level):** Focus on testing API endpoints through the `TestClient`. These tests validate the request/response cycle, authentication/authorization, and interaction with the database via the API layer. Located in `backend/tests/`.

### Key Fixtures (`backend/tests/conftest.py`)
*   `db_engine`: Manages the PostgreSQL test database lifecycle (create/drop).
*   `db_session`: Provides a transactional SQLAlchemy session for each test function, ensuring rollback after completion.
*   `client`: Provides a FastAPI `TestClient` instance.
*   `mock_current_user` / `mock_admin_user`: Mocks the `get_current_user` dependency to simulate authenticated users with specific roles/permissions.
*   `auth_client` / `admin_client`: Combines `client` with mocked authentication.
*   `seed_*` fixtures (e.g., `seed_test_user`): Create specific data records needed for tests.

## Frontend Testing (TypeScript/React) - Sprint 3/4

*   **Framework:** Jest + React Testing Library (RTL).
*   **Test Types:**
    *   **Component Tests:** Test individual React components in isolation, verifying rendering and user interactions.
    *   **Integration Tests:** Test interactions between multiple components.
*   **Mocking:** Mock API calls using libraries like `msw` (Mock Service Worker) or Jest mocks.

## End-to-End (E2E) Testing - Sprint 4

*   **Framework:** Cypress.
*   **Goal:** Simulate real user workflows across the entire application stack (frontend interacting with backend).
*   **Scope:** Cover critical user journeys like signup, login, club creation, joining clubs, recording transactions.

## Test Execution

*   Tests can be run locally using the `pytest` command in the `backend` directory.
*   CI/CD pipeline (to be configured) will automatically run tests on code pushes/pull requests.

## Future Considerations

*   Code coverage reporting.
*   Performance testing.
*   Security testing.