# System Patterns

This file documents recurring patterns and standards used in the project.
2025-05-05 08:33:00 - Initial creation based on codebase analysis.
2025-05-10 13:26:00 - Updated with frontend patterns based on detailed code analysis.

## Backend Coding Patterns

* **Async/Await Pattern**:
  * All database operations use async SQLAlchemy
  * API endpoints are async functions
  * Service functions are async and orchestrate CRUD operations

* **Dependency Injection**:
  * FastAPI dependency system for database sessions
  * Authentication and authorization via dependencies
  * Service dependencies injected where needed

* **Error Handling**:
  * Consistent use of HTTPException with appropriate status codes
  * Detailed error messages with proper logging
  * Try/except blocks with specific exception handling

* **Validation**:
  * Pydantic models for request/response validation
  * Type hints throughout the codebase
  * Explicit validation in service functions

* **Logging**:
  * Consistent logging patterns with appropriate levels
  * Contextual information in log messages
  * Error details captured in exception handling

## Frontend Coding Patterns

* **Component Structure**:
  * Functional components with TypeScript
  * Custom hooks for reusable logic
  * Composition over inheritance

* **Form Handling**:
  * Controlled components for form inputs
  * Form validation with schema-based approach
  * Consistent error display patterns

* **Authentication Integration**:
  * Auth0 React SDK for authentication
  * Protected routes with role-based access
  * Organization support for multi-tenancy

* **API Communication**:
  * Centralized API client
  * Type-safe request/response handling
  * Error handling middleware

## Architectural Patterns

* **Backend Layered Architecture**:
  * API Layer: FastAPI routers and endpoints
  * Service Layer: Business logic and orchestration
  * CRUD Layer: Database operations
  * Model Layer: SQLAlchemy models

* **Frontend Architecture**:
  * Feature-based organization
  * Shared UI component library
  * Route-based code splitting
  * Context providers for global state

* **Repository Pattern**:
  * CRUD modules encapsulate database operations
  * Service layer never directly manipulates models
  * Consistent interface for database operations

* **Unit Value Accounting**:
  * NAV (Net Asset Value) calculation
  * Unit-based equity tracking
  * Transaction processing affects unit balances

* **Multi-tenancy**:
  * Club-based isolation of data
  * Role-based access control within clubs
  * User membership determines access

* **Event-based Transactions**:
  * Financial transactions trigger calculations
  * Unit value history tracks changes over time
  * Member equity calculated based on unit holdings

## Integration Patterns

* **API Contract**:
  * Consistent endpoint structure
  * Standardized response formats
  * Error handling conventions

* **State Management**:
  * Server state vs. UI state separation
  * Caching and invalidation strategies
  * Optimistic updates for better UX

* **Data Fetching**:
  * React Query for server state
  * Loading/error state handling
  * Pagination and infinite scrolling

## Testing Patterns

* **Backend Testing**:
  * Pytest fixtures for database setup
  * Alembic migrations in test environment
  * Isolated test database
  * Mock external services (e.g., Alpha Vantage API)
  * Mock database sessions for unit tests
  * Mock authentication for API tests

* **Frontend Testing**:
  * Component testing with React Testing Library
  * Mock API responses
  * User interaction testing

* **Test Categories**:
  * Unit tests for core logic
  * Integration tests for API endpoints
  * End-to-end tests for critical user flows