# Project Summary: MGA Wealth Management Platform

## 1. Introduction

**Goal:** To build a comprehensive Investment Club Management Platform.

**Current Status:** The project is in the early stages of development. The primary focus has been on establishing the foundational backend database structure and setting up the basic frontend application shell with authentication.

## 2. Architecture Overview

This is a full-stack web application featuring:

*   **Backend:** Python with the FastAPI framework.
*   **Frontend:** TypeScript with the React library and Vite build tool.
*   **Database:** PostgreSQL.
*   **Authentication:** Auth0.

The project follows a monorepo structure with distinct `backend` and `frontend` directories.

**High-Level Architecture:**

```mermaid
graph TD
    A[User Browser] --> F[Frontend (React/Vite)];
    F --> B[Backend API (FastAPI)];
    F --> AUTH[Auth0];
    B --> D[Database (PostgreSQL)];
    B --> AUTH;
    subgraph "Project Repository"
        direction LR
        F
        B
    end
```

## 3. Backend Details

*   **Stack:**
    *   Language/Framework: Python / FastAPI
    *   ORM: SQLAlchemy
    *   Database Migrations: Alembic
    *   Data Validation: Pydantic
    *   Database Driver: psycopg2 / asyncpg (suggesting PostgreSQL)
    *   Other: Uvicorn (ASGI Server), python-dotenv
*   **Status:**
    *   Core database models are defined in `backend/models/`. See `database-schema.md` for a visual representation.
    *   An initial database migration has been created using Alembic (`backend/migrations/`).
    *   API endpoint implementation is largely pending. The current `backend/main.py` is a basic placeholder.
*   **Setup (Assumed):**
    ```bash
    # Navigate to backend directory
    cd backend
    # Create/activate a virtual environment (e.g., venv)
    python -m venv .venv
    source .venv/bin/activate # or .venv\Scripts\activate on Windows
    # Install dependencies
    pip install -r requirements.txt
    ```
*   **Running (Development):**
    ```bash
    uvicorn backend.main:app --reload --port 8000
    ```

## 4. Frontend Details

*   **Stack:**
    *   Language/Library: TypeScript / React
    *   Build Tool: Vite
    *   UI Library: Chakra UI
    *   State Management: Zustand
    *   Data Fetching: TanStack Query (React Query)
    *   Routing: React Router
    *   Authentication: Auth0 React SDK
    *   Styling: Emotion, CSS Modules/Global CSS
    *   Icons: React Icons
    *   Animation: Framer Motion
    *   Makret Data: Alpha Vantage
*   **Status:**
    *   Basic application structure (`frontend/src/App.tsx`) is set up.
    *   Routing between a Landing page (`frontend/src/pages/Landing.tsx`) and a Dashboard page (`frontend/src/pages/Dashboard.tsx`) is configured.
    *   Auth0 integration for login/logout and route protection is implemented.
    *   The actual content and functionality of the pages are placeholders pending development.
    *   Connection to the backend API is pending API development.
    *   Alpha Vantage integration is pending API development.
*   **Setup:**
    ```bash
    # Navigate to frontend directory
    cd frontend
    # Install dependencies
    npm install
    ```
*   **Running (Development):**
    ```bash
    npm run dev
    ```

## 5. Database

*   The detailed database schema (Entity Relationship Diagram) can be found in `database-schema.md`.
*   SQLAlchemy is used as the ORM in the backend.
*   Alembic is configured for managing database schema migrations. Ensure the database connection string is correctly configured in `alembic.ini` and `backend/migrations/env.py` before running migrations (`alembic upgrade head`).

## 6. Authentication

*   Auth0 is used as the identity provider for user authentication and authorization.
*   The frontend utilizes the `@auth0/auth0-react` SDK to handle the login flow, manage user sessions, and protect routes.
*   Backend API endpoints will need to be secured, typically by validating JWTs (JSON Web Tokens) issued by Auth0. This integration is pending API development.

## 7. Project Status Summary

The project is in its **initial development phase**.

*   **Completed:**
    *   Definition of core database models (SQLAlchemy).
    *   Setup of Alembic and creation of the initial database migration.
    *   Basic frontend application structure using Vite and React/TypeScript.
    *   Setup of frontend routing (Landing/Dashboard).
    *   Integration of Auth0 SDK in the frontend for authentication flow.
*   **Next Steps:**
    *   Implement backend API endpoints using FastAPI (CRUD operations for models, business logic).
    *   Secure backend API endpoints using Auth0 JWT validation.
    *   Develop frontend components and UI based on Chakra UI.
    *   Implement state management logic using Zustand.
    *   Integrate frontend pages with the backend API using TanStack Query for data fetching.
    *   Refine and expand database models and migrations as features are developed.
    *   Write unit and integration tests for both backend and frontend.