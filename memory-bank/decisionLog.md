# Decision Log

This file records architectural and implementation decisions using a list format.
2025-05-05 08:33:00 - Initial creation based on codebase analysis.

## Decision: Async SQLAlchemy for Database Operations

* **Rationale**: 
  * Improved scalability and performance for concurrent requests
  * Better resource utilization during I/O-bound operations
  * Consistent with FastAPI's async-first approach

* **Implementation Details**:
  * Using SQLAlchemy's async extension
  * AsyncSession for all database operations
  * Async context managers for session management
  * Explicit await for all database operations

## Decision: Auth0 for Authentication

* **Rationale**:
  * Secure, industry-standard authentication service
  * Offloads complex auth management to a specialized service
  * Provides JWT tokens with standard claims
  * Supports social logins and enterprise connections

* **Implementation Details**:
  * JWT validation using JWKS from Auth0
  * Token caching to reduce external API calls
  * Mapping Auth0 users to internal user records
  * Email claim required in tokens

## Decision: Unit-based Equity Tracking

* **Rationale**:
  * Standard approach for investment clubs
  * Allows for fair distribution of gains/losses
  * Supports partial ownership and flexible contributions
  * Simplifies member equity calculations

* **Implementation Details**:
  * NAV calculation based on asset prices and cash
  * Unit value history tracked over time
  * Member transactions affect unit balances
  * Deposits issue new units, withdrawals redeem units

## Decision: Multi-Fund Structure

* **Rationale**:
  * Allows clubs to organize investments by strategy or asset class
  * Supports different allocation strategies
  * Enables tracking performance by fund

* **Implementation Details**:
  * Funds belong to clubs
  * Fund splits define allocation percentages
  * Positions and transactions linked to specific funds
  * Cash tracked at both club and fund levels

## Decision: Layered Architecture

* **Rationale**:
  * Clear separation of concerns
  * Testability of individual components
  * Maintainability and code organization
  * Consistent patterns across the application

* **Implementation Details**:
  * API Layer: FastAPI routers and endpoints
  * Service Layer: Business logic and orchestration
  * CRUD Layer: Database operations
  * Model Layer: SQLAlchemy models