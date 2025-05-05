# backend/core/session.py

import logging
from typing import AsyncGenerator
from fastapi import HTTPException

# Assuming SQLAlchemy and FastAPI are installed
try:
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        async_sessionmaker,
        AsyncSession,
        AsyncEngine,
    )
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    print("WARNING: SQLAlchemy not found. Session management will not work.")
    # Define dummy types/classes if needed for syntax validity
    class AsyncSession: pass
    class AsyncEngine: pass
    class SQLAlchemyError(Exception): pass
    def create_async_engine(*args, **kwargs) -> AsyncEngine: return AsyncEngine()
    def async_sessionmaker(*args, **kwargs):
        class DummySessionFactory:
            async def __call__(self) -> AsyncSession: return AsyncSession()
        return DummySessionFactory()

# Import the function to get the database URL
try:
    from backend.core.database import get_async_url
except ImportError:
    print("WARNING: Could not import get_async_url. Database connection cannot be established.")
    def get_async_url() -> str: return "postgresql+asyncpg://user:pass@host:port/db" # Dummy URL

# Configure logging
log = logging.getLogger(__name__)

# --- Engine and Session Factory Setup ---
# These should be initialized once when the application starts.
# Placing them here makes them available for the dependency function.

# Initialize engine and session_factory to None initially
async_engine: AsyncEngine | None = None
SessionFactory: async_sessionmaker[AsyncSession] | None = None

def initialize_database():
    """Initializes the async engine and session factory."""
    global async_engine, SessionFactory
    try:
        db_url = get_async_url()
        # Consider pool settings for production (e.g., pool_size, max_overflow)
        # For simplicity here, using defaults. Echo can be turned on for debugging.
        async_engine = create_async_engine(db_url, echo=False) # Set echo=True for SQL logging
        SessionFactory = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False # Important for async usage
        )
        log.info("Database engine and session factory initialized successfully.")
    except Exception as e:
        log.exception("Failed to initialize database engine or session factory.")
        # Depending on app structure, might want to raise or exit here
        raise RuntimeError("Database initialization failed") from e

# Call initialize_database() when this module is imported,
# or call it explicitly during application startup (e.g., in main.py @app.on_event("startup"))
# Calling it here for simplicity in this example.
# initialize_database()
# NOTE: If running with multiple workers (like gunicorn), initializing here might
# create multiple engine instances. It's often better to initialize in a startup event.
# We will assume it's called during app startup for now.


# --- Dependency Function ---

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session with transaction management.

    Yields:
        An AsyncSession instance.

    Handles commit, rollback, and closing of the session.
    """
    if SessionFactory is None:
        # This should ideally not happen if initialize_database() is called at startup
        log.error("SessionFactory not initialized. Cannot create DB session.")
        # Raising RuntimeError as this indicates a fundamental setup issue
        raise RuntimeError("Database session factory has not been initialized.")

    # Create a new session for the request
    session: AsyncSession = SessionFactory()
    log.debug(f"DB Session created: {session}")

    try:
        # Start transaction (optional, depends if autocommit=False is set on sessionmaker/engine)
        # await session.begin() # Often managed implicitly by session context

        # Provide the session to the route/dependency
        yield session

        # If no exceptions were raised, commit the transaction
        await session.commit()
        log.debug(f"DB Session committed: {session}")

    except SQLAlchemyError as db_exc:
        # Catch specific SQLAlchemy errors or general exceptions
        log.exception(f"Database error occurred in session {session}. Rolling back.")
        await session.rollback()
        # Re-raise the original exception or a specific HTTPException
        # Re-raising allows FastAPI's exception handlers to catch it
        raise HTTPException(
            status_code=500, # Or map specific DB errors to HTTP codes
            detail=f"Database error: {db_exc}"
        ) from db_exc
    except HTTPException as http_exc:
        # If an HTTPException was raised within the endpoint/service using the session
        log.warning(f"HTTPException occurred during request using session {session}. Rolling back. Detail: {http_exc.detail}")
        await session.rollback()
        raise http_exc # Re-raise the HTTPException
    except Exception as e:
        # Catch any other unexpected errors
        log.exception(f"Unexpected error occurred in session {session}. Rolling back.")
        await session.rollback()
        # Re-raise as a generic internal server error
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred: {e}"
        ) from e
    finally:
        # Always close the session when done
        await session.close()
        log.debug(f"DB Session closed: {session}")

