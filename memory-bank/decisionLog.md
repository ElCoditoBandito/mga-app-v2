# Decision Log

[2025-04-20 13:58:00] - **Test Fixture Design for Fund Memberships**

Identified and fixed issues with test fixtures for fund membership tests by:
1. Adding missing fixtures to test functions to ensure proper database relationships
2. Creating a new `seed_test_club_membership` fixture to establish club membership for fund members
3. Ensuring proper parameter passing in CRUD function calls

This decision reinforces the importance of proper test fixture design in maintaining the integrity of the authorization model across the application.

[2025-04-20 10:02:10] - **TestClient Initialization Refactoring**

Modified the client fixture in conftest.py to import the app inside the fixture function rather than at the module level. This ensures the TestClient is always created with the fully configured application instance, which should resolve the persistent 404 errors in API tests.

Key changes:
1. Removed the global import of app from the top of conftest.py
2. Added the import inside the client fixture function
3. Modified the client fixture to return a dictionary with both app and client
4. Updated all other fixtures that use the client fixture to extract the app and client from the dictionary

This change ensures that routers are fully registered before the TestClient is created.

This file records architectural and implementation decisions using a list format.
2025-04-16 01:24:56 - Log of updates made.
2025-04-18 13:40:00 - Updated to reflect library version compatibility decisions.
2025-04-18 17:35:00 - Updated to reflect full completion of Sprint 1 with all tests passing.
2025-04-18 19:54:00 - Updated to reflect Sprint 2 implementation decisions.

2025-04-18 16:10:00 - Updated to reflect completion of all Sprint 1 unit tests.

*
*   [2025-04-18 19:54:00] - Complete implementation of all Sprint 2 components and plan for comprehensive testing.

*   [2025-04-18 17:35:00] - Complete all Sprint 1 requirements with the addition of the missing test for `get_membership_by_club_and_user`.

*   [2025-04-18 17:48:00] - Create detailed execution plan for Sprint 2 with prioritized implementation order and clear task breakdowns.

## Decision

*   [2025-04-18 23:00:00] - Migrate from Pydantic v1 style `@validator` decorators to v2 style `@field_validator` decorators
*   [2025-04-18 19:54:00] - Implement consistent validation patterns across all investment-related schemas using Pydantic validators.
*   [2025-04-18 19:54:00] - Implement position updates within transaction creation to maintain data consistency.
*   [2025-04-18 19:54:00] - Use a hierarchical role system for fund memberships (manager > analyst > readonly).
*   [2025-04-18 19:54:00] - Implement one-to-one relationship between Funds and Portfolios for simplified management.
*   [2025-04-18 17:48:00] - Prioritize Sprint 2 implementation in the following order: Funds → Portfolios → Positions → Transactions → Income/Performance Snapshots → (Optional) Discussions.
*   [2025-04-18 17:48:00] - Use mock data for the ASSET model in Sprint 2; defer Alpha Vantage integration to Sprint 3.
*   [2025-04-18 17:48:00] - Implement role-based authorization for investment operations (Fund Owner/Manager for write access, Fund Member for read access).
*   [2025-04-18 17:48:00] - Implement basic validation using Pydantic validators for investment-related models.
*   [2025-04-18 13:40:00] - Update codebase to be compatible with SQLAlchemy 2.0 and Pydantic V2.
*   [2025-04-18 13:40:00] - Utilize the `run_all_migrations.py` script for managing database migrations across development and test environments.
*   [2025-04-16 00:27:24] - Initialize Memory Bank for project tracking.
*   [2025-04-16 00:39:19] - Adopt Auth0 for authentication with JWT verification in backend.
*   [2025-04-16 00:39:19] - Implement user creation flow where frontend triggers `POST /users` after Auth0 signup.
*   [2025-04-16 00:39:19] - Implement role-based authorization for Club management.
*   [2025-04-16 01:10:28] - Adopt a structured API architecture with separate modules for routes, schemas, and CRUD operations.
*   [2025-04-16 01:10:28] - Implement JWT verification with JWKS caching for performance.
*   [2025-04-16 01:10:28] - Use FastAPI dependencies for authentication and authorization checks.
*   [2025-04-16 01:24:56] - Implement comprehensive unit testing with pytest and fixtures.
*   [2025-04-16 01:24:56] - Enhance API documentation with summary and description parameters.

## Rationale

*   **Pydantic v1 to v2 Migration:** The project is using Pydantic v2.11.3, but still has validators using the deprecated v1 style `@validator` decorator. These deprecated validators are generating warnings in tests. Migrating to v2 style validators will future-proof the code as v1 style validators will be removed in Pydantic v3.0.

*   **Consistent Validation Patterns:** Ensures data integrity across all investment-related operations by validating input data at the schema level before it reaches the database. Prevents invalid data (e.g., negative quantities, future dates) from being processed.
*   **Position Updates in Transactions:** Maintains data consistency by automatically updating position data when transactions are created. This ensures that position data always reflects the current state based on all transactions.
*   **Hierarchical Role System:** Provides a clear authorization model for fund operations where managers have full access, analysts have intermediate access, and readonly members have basic viewing privileges.
*   **One-to-One Fund-Portfolio Relationship:** Simplifies the data model and business logic by ensuring each fund has exactly one portfolio. This matches the business requirement and reduces complexity.
*   **Sprint 2 Implementation Prioritization:** Establishes a logical progression from foundational components (Funds) to more dependent features (Transactions, Income). This approach ensures that each component has its prerequisites in place before implementation.
*   **Mock Asset Data:** Simplifies development by deferring external API integration to Sprint 3, allowing focus on core investment functionality first. Provides a clean separation of concerns between data modeling and external data fetching.
*   **Investment Authorization Rules:** Extends the role-based security model established in Sprint 1 to investment operations, ensuring proper access control where Fund Owners/Managers have write access and Fund Members have read-only access.
*   **Pydantic Validation:** Ensures data integrity by validating investment-related data (e.g., positive quantities, valid transaction types) at the schema level before it reaches the database.
*   **SQLAlchemy 2.0 and Pydantic V2 Compatibility:** Ensures the codebase uses current best practices and avoids deprecated features, preventing future issues when libraries remove deprecated functionality. Addresses warnings in test output for better code quality.
*   **Migration Script Usage:** Provides a consistent, reliable way to apply database schema changes across both development and test environments, with built-in error handling and logging.
*   **Memory Bank:** Maintain project context, track progress, and log decisions effectively throughout development.
*   **Auth0 Integration:** Provides secure, reliable authentication without building custom auth system. Appropriate for MVP.
*   **User Creation Flow:** Simplifies MVP by leveraging Auth0's signup process, then syncing to our database. Supports whitelisting approach.
*   **Role-based Authorization:** Ensures proper security model where only authorized users can perform sensitive operations.
*   **Structured API Architecture:** Separates concerns for better maintainability and testability. Routes handle HTTP concerns, schemas handle validation, and CRUD operations handle database interactions.
*   **JWT Verification with JWKS Caching:** Improves performance by reducing the number of HTTP requests to Auth0 for JWKS retrieval.
*   **FastAPI Dependencies:** Provides a clean, reusable way to implement authentication and authorization checks across multiple endpoints.
*   **Comprehensive Unit Testing:** Ensures code quality, validates business logic, and prevents regressions. Facilitates future development by providing a safety net for changes.
*   **Enhanced API Documentation:** Improves developer experience by providing clear, concise information about API endpoints directly in the Swagger UI.

## Implementation Details

*   **Pydantic v1 to v2 Migration:**
    *   Update import statements in affected files to include `field_validator` instead of `validator`
    *   Replace all `@validator` decorators with `@field_validator` decorators
    *   Update validator function signatures to use the new v2 style parameter structure
    *   Affected files:
        *   `backend/schemas/position.py`
        *   `backend/schemas/transaction.py`
        *   `backend/schemas/income.py`
        *   `backend/schemas/performance_snapshot.py`

*   **Sprint 2 Implementation:**
    *   Implemented schemas, CRUD operations, and API endpoints for all investment-related components:
        *   Funds and Fund Memberships
        *   Portfolios
        *   Assets and Positions
        *   Transactions
        *   Income and Performance Snapshots
    *   Applied consistent validation patterns across all schemas using Pydantic validators
    *   Implemented automatic position updates within transaction creation
    *   Updated main.py to include all new API routes with appropriate tags

*   **Investment Authorization Model:**
    *   Implemented a hierarchical role system for fund memberships (manager > analyst > readonly)
    *   Fund Managers have full access to create, update, and delete funds, record transactions, and manage fund memberships
    *   Fund Members have read-only access to fund details, portfolio information, and transaction history
    *   Authorization is implemented using FastAPI dependencies similar to the Club authorization model from Sprint 1

*   **Data Relationships:**
    *   Implemented one-to-one relationship between Funds and Portfolios
    *   Implemented many-to-many relationship between Portfolios and Assets through Positions
    *   Implemented one-to-many relationship between Portfolios and Transactions
    *   Implemented one-to-many relationship between Portfolios and Income records
    *   Implemented one-to-many relationship between Funds/Portfolios and Performance Snapshots

*   **Sprint 2 Plan:**
    *   Created a detailed execution plan in `SPRINT2_PLAN.md` with task breakdowns, implementation order, and diagrams.
    *   Defined clear actions for each component (Funds, Portfolios, Positions, Transactions, Income, Performance Snapshots).
    *   Included implementation flow diagrams, authorization flow, and data flow for investment operations.
    *   Established a testing strategy for investment-related endpoints.

*   **Mock Asset Data Strategy:**
    *   Asset data will be created and managed through the API during Sprint 2.
    *   Alpha Vantage integration for real-time market data will be deferred to Sprint 3.
    *   The Asset model will include fields for symbol, name, asset_type, and current_price to support basic investment operations.

*   **SQLAlchemy 2.0 Compatibility:**
    *   Updated imports in `backend/dependencies/database.py` and `backend/models/base.py` to use `sqlalchemy.orm.declarative_base` instead of `sqlalchemy.ext.declarative.declarative_base`.
*   **Pydantic V2 Compatibility:**
    *   Updated Pydantic models in `backend/schemas/user.py`, `backend/schemas/club.py`, and `backend/schemas/membership.py` to use `model_config = {"from_attributes": True}` instead of inner `class Config` with `orm_mode = True`.
    *   Updated CRUD operations in `backend/crud/club.py` and `backend/crud/user.py` to use `.model_dump()` instead of `.dict()` for Pydantic models.
*   **Migration Script:**
    *   The `backend/scripts/run_all_migrations.py` script handles running Alembic migrations on both development and test databases.
    *   Provides detailed HTML error logging if migrations fail.
    *   Temporarily sets the correct database URL for the test environment.
*   **Memory Bank:** Created standard Memory Bank files: `productContext.md`, `activeContext.md`, `progress.md`, `decisionLog.md`, `systemPatterns.md`.
*   **Auth0 Integration:** Implemented JWT verification in `backend/dependencies/auth.py`. Configured Auth0 Audience.
*   **User Creation:** `POST /users` endpoint creates user record in database after Auth0 signup. Frontend will handle this flow.
*   **Authorization Rules:**
    *   Club Deletion: Only Club Owner.
    *   Membership Management: Club Owner or Admin roles.
*   **API Structure:**
    *   `api/` directory contains route handlers organized by resource.
    *   `schemas/` directory contains Pydantic models for request/response validation.
    *   `crud/` directory contains database operations.
    *   `dependencies/` directory contains reusable FastAPI dependencies.
*   **JWT Verification:**
    *   Implemented JWKS fetching and caching.
    *   Created `get_current_user` dependency for protecting routes.
    *   Added support for role-based access control.
*   **Database Session Management:**
    *   Implemented database session dependency in `backend/dependencies/database.py`.
    *   Used SQLAlchemy for ORM operations.
*   **Unit Testing Framework:**
*   **Completed Sprint 1 Test Coverage:**
    *   Added the missing test for `get_membership_by_club_and_user` function to ensure complete test coverage.
    *   Verified all 65 tests are now passing successfully.
    *   Ensured all Sprint 1 requirements are fully met and validated.

    *   Created `conftest.py` with reusable fixtures for database session, authentication, and test client.
    *   Implemented mock objects for database and authentication dependencies.
    *   Structured tests to verify CRUD operations and API endpoints separately.
    *   Added tests for authorization checks and edge cases.
    *   Completed comprehensive unit tests for all Membership API endpoints:
        *   Added tests for GET, PUT, DELETE endpoints and failure scenarios for POST.
        *   Ensured test coverage for all authorization rules and edge cases.
*   **API Documentation:**
    *   Added `summary` and `description` parameters to all route decorators.
    *   Ensured documentation clearly explains endpoint purpose, authorization requirements, and expected behavior.
    *   Maintained existing docstrings for code-level documentation.