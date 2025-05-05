# backend/core/database.py

"""
Handles database configuration loading and defines the SQLAlchemy Base.

- Reads database connection URLs from environment variables via dotenv.
- Provides functions to retrieve the appropriate Sync/Async URL based on TESTING env var.
- Defines the shared SQLAlchemy Declarative Base for models.
- Does NOT create engines or sessions here.
"""

import logging
import os

from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base

# --- Logging Setup ---
log = logging.getLogger(__name__)
# Basic config can be done here or in the main application/conftest
# logging.basicConfig(level=logging.INFO)

# --- Load Environment Variables ---
# Load .env file when this module is first imported.
# Subsequent calls to get_sync_url/get_async_url will read the *current* env var state.
load_dotenv()


# --- Shared Declarative Base ---

# All SQLAlchemy models should inherit from this Base
Base = declarative_base()

# --- URL Retrieval Functions ---

def get_sync_url() -> str:
    """
    Returns the appropriate Synchronous Database URL based on the TESTING env var.
    Raises ValueError if the required URL is not set.
    """
    testing = os.getenv("TESTING", "false").lower() == "true"
    url: str | None = None

    if testing:
        url = os.getenv("SYNC_TEST_DB")
        if not url:
            log.error("SYNC_TEST_DB environment variable is not set for testing")
            raise ValueError("SYNC_TEST_DB must be set for testing")
    else:

        url = os.getenv("DATABASE_URL") # Primary sync URL for dev/prod (used by Alembic)
        if not url:
            log.error("DATABASE_URL environment variable is not set for dev/prod")
            # Optionally construct from parts if needed as fallback
            # db_user = os.getenv("DB_USER", "postgres")
            # ... construct url ...
            raise ValueError("DATABASE_URL must be set for dev/prod")

    return url


def get_async_url() -> str:
    """
    Returns the appropriate Asynchronous Database URL based on the TESTING env var.
    Raises ValueError if the required URL is not set.
    """
    testing = os.getenv("TESTING", "false").lower() == "true"
    url: str | None = None

    if testing:

        url = os.getenv("ASYNC_TEST_DB")
        if not url:
            log.error("ASYNC_TEST_DB environment variable is not set for testing")
            raise ValueError("ASYNC_TEST_DB must be set for testing")
    else:

        url = os.getenv("ASYNC_DATABASE_URL") # Primary async URL for dev/prod
        if not url:
            log.error("ASYNC_DATABASE_URL environment variable is not set for dev/prod")
            # Optionally construct from parts if needed as fallback
            # db_user = os.getenv("DB_USER", "postgres")
            # ... construct url ...
            raise ValueError("ASYNC_DATABASE_URL must be set for dev/prod")


    return url

# --- Example Usage (for clarity, not executed on import) ---
# if __name__ == "__main__":
#     print("Running database.py directly...")
#     # Example of how other modules would use these functions:
#     try:
#         sync_db_url = get_sync_url()
#         async_db_url = get_async_url()
#         print(f"Retrieved Sync URL: {sync_db_url}")
#         print(f"Retrieved Async URL: {async_db_url}")
#     except ValueError as e:
#         print(f"Error getting URLs: {e}")

