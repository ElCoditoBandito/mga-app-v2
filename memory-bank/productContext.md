# Product Context

This file provides a high-level overview of the project and the expected product that will be created. Initially it is based upon projectBrief.md (if provided) and all other available project-related information in the working directory. This file is intended to be updated as the project evolves, and should be used to inform all other modes of the project's goals and context.
2025-05-05 08:32:00 - Initial creation based on project overview and codebase analysis.

## Project Goal

The goal is to build a backend API (using FastAPI) for an MVP of a social investment club dashboard. The platform allows investment clubs to:

* Manage members with different roles (Admin, Member, ReadOnly)
* Manually track investments (stocks, ETFs, options)
* Manually track club bank accounts (for expenses, member deposits/withdrawals)
* Manually track fund transfers (bank-to-brokerage)
* Distribute transfers across multiple internal funds based on club settings
* Calculate member equity using a unit value system (NAV per unit)

The long-term vision includes more social features and potentially direct brokerage integration.

## Key Features

* **User Authentication/Authorization**:
  * Auth0 integration for secure authentication
  * Role-based access control (Admin, Member, ReadOnly)
  * Multi-tenancy support at the data level

* **Club Management**:
  * Create and manage clubs
  * Add/update/remove members
  * Update member roles

* **Financial Management**:
  * Manual entry of investment transactions (buy/sell stocks, options)
  * Track cash transactions (deposits, withdrawals, expenses)
  * Fund transfers between bank and brokerage accounts
  * Fund split management for distributing transfers

* **Accounting System**:
  * Automatic calculation of fund positions and cash balances
  * NAV (Net Asset Value) calculation per club
  * Unit-based equity tracking for members
  * Member equity calculation

* **Reporting**:
  * Portfolio summary
  * Member statements
  * Performance tracking

## Overall Architecture

* **Technology Stack**:
  * Database: PostgreSQL
  * Backend Framework: Python, FastAPI
  * ORM: SQLAlchemy (Async version)
  * Migrations: Alembic
  * Data Validation/Serialization: Pydantic
  * Authentication: Auth0
  * Testing: Pytest, pytest-asyncio, unittest.mock

* **Architecture Pattern**:
  * Layered architecture:
    * API Layer (Routers/Endpoints)
    * Service Layer (Business Logic)
    * CRUD Layer (Database Operations)
    * Model Layer (Database Schema)
  * Async patterns throughout for scalability
  * Dependency injection for services and database sessions

* **Data Model**:
  * Core entities: User, Club, ClubMembership, Fund, Asset, Position, Transaction, MemberTransaction, UnitValueHistory, FundSplit
  * Comprehensive relationships between entities
  * Enums for type safety (TransactionType, AssetType, ClubRole, etc.)