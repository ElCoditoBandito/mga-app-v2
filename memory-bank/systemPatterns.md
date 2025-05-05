# System Patterns *Optional*

This file documents recurring patterns and standards used in the project.
It is optional, but recommended to be updated as the project evolves.
2025-04-16 00:27:30 - Log of updates made.
2025-04-18 17:35:00 - Updated to reflect full completion of Sprint 1 with all tests passing.
2025-04-18 16:11:00 - Updated to reflect testing patterns established in Sprint 1.
2025-04-18 17:50:00 - Updated to include patterns for investment-related components in Sprint 2.

*

## Coding Patterns

*   Backend: Follow FastAPI best practices, use SQLAlchemy ORM patterns, Pydantic for validation.
*   Frontend: Follow React best practices, utilize hooks, component-based architecture. TypeScript for type safety.
*   Investment Models:
    *   Use Pydantic validators for investment-related data (e.g., positive quantities, valid transaction types).
    *   Implement transaction-driven position updates (positions reflect transaction history).
    *   Use mock data for assets during Sprint 2, with Alpha Vantage integration planned for Sprint 3.
    *   Ensure proper relationships between models (Fund → Portfolio → Positions/Transactions).

## Architectural Patterns

*   Monorepo structure.
*   RESTful API design for backend.
*   Client-side rendering (CSR) with React.
*   Token-based authentication (JWT with Auth0).
*   Service layer for API calls in frontend (using TanStack Query).
*   State management with Zustand in frontend.
*   Investment hierarchy: Club → Fund → Portfolio → Positions/Transactions.
*   Role-based access control for investment operations.
*   Transaction-driven position updates (positions reflect transaction history).
*   Performance snapshots for point-in-time portfolio valuation.

*   Backend: Comprehensive unit tests with `pytest` (65 passing tests).

## Testing Patterns

*   Backend: Unit tests with `pytest`.
    *   Test fixtures in `conftest.py` for database sessions, authentication, and test clients.
    *   Separate tests for CRUD functions and API endpoints.
    *   Mock dependencies using `unittest.mock.patch` to isolate components.
    *   Test both success and failure scenarios for all endpoints.
    *   Ensure proper fixture dependencies for authorization tests:
        *   Include all required fixtures in test functions to establish complete database relationships
        *   For nested resources (e.g., fund memberships), ensure parent-child relationships are properly set up
        *   For authorization tests, ensure the authenticated user has the appropriate memberships/roles
    *   Test authorization rules and edge cases.
*   Frontend: Component tests with React Testing Library.
*   End-to-end tests with Cypress (Sprint 4).
*   Integration tests for API (Sprint 4).