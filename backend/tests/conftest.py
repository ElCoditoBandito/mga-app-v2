# tests/conftest.py

import asyncio
import logging
import os
import sys
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine as SyncEngine
from sqlalchemy.exc import ProgrammingError, InvalidRequestError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(name)s:%(lineno)d - %(message)s'
)
logging.getLogger('alembic').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
log = logging.getLogger(__name__) # Logger for conftest messages

# --- Environment Loading ---
# This runs first due to autouse=True

@pytest.fixture(scope="session", autouse=True)
def load_env() -> None:
    """Loads environment variables from .env and sets TESTING flag."""

    load_dotenv()
    os.environ['TESTING'] = 'True'


# --- Database URL Fixtures ---
# These depend implicitly on load_env having run

@pytest.fixture(scope="session")
def sync_test_db_url() -> str:
    """Fixture to get the sync test database URL."""

    # Import URL function *inside* the fixture to ensure TESTING is set
    from backend.core.database import get_sync_url
    try:
        url = get_sync_url()

        return url
    except ValueError as e:
        pytest.fail(f"Failed to get sync test DB URL: {e}")
    except ImportError:
         pytest.fail("Could not import get_sync_url from backend.core.database")


@pytest.fixture(scope="session")
def async_test_db_url() -> str:
    """Fixture to get the async test database URL."""

    # Import URL function *inside* the fixture
    from backend.core.database import get_async_url
    try:
        url = get_async_url()

        return url
    except ValueError as e:
        pytest.fail(f"Failed to get async test DB URL: {e}")
    except ImportError:
        pytest.fail("Could not import get_async_url from backend.core.database")


# --- Core Database Setup and Migration Fixture ---

@pytest.fixture(scope="session")
def db_setup_and_migration(sync_test_db_url: str) -> Generator[SyncEngine, None, None]:
    """
    Session-scoped fixture:
    1. Creates sync engine using the retrieved test URL.
    2. Imports Base *after* engine creation.
    3. Cleans DB schema (drops tables).
    4. Runs Alembic migrations.
    5. Yields the engine.
    6. Cleans DB schema (drops tables) on teardown.
    """

    sync_engine = create_engine(sync_test_db_url, echo=False)


    # --- Import Base HERE, after load_env and engine creation ---
    # This ensures metadata population happens *after* the initial setup phases
    try:
        from backend.core.database import Base
   
        # Log initial state right after import inside the fixture

    except ImportError:
        pytest.fail("Could not import SQLAlchemy Base from backend.core.database inside db_setup_and_migration")
    # -----------------------------------------------------------

    # --- Alembic Configuration ---
    alembic_ini_path = os.path.join('backend', 'alembic.ini')
    alembic_script_location = os.path.join('backend', 'migrations')

    if not os.path.exists(alembic_ini_path):
        pytest.fail(f"Alembic config file not found at: {alembic_ini_path}")
    if not os.path.exists(alembic_script_location):
         pytest.fail(f"Alembic script location not found at: {alembic_script_location}")

    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", alembic_script_location)
    alembic_cfg.set_main_option("sqlalchemy.url", sync_test_db_url)
    log.info("Alembic configured for test database.")

    try:
        # --- Pre-Migration Cleanup ---

        # Log metadata state *again* right before drop_all

        with sync_engine.begin() as conn:

            Base.metadata.drop_all(bind=conn)

            try:
                conn.execute(text("DROP TABLE IF EXISTS alembic_version;"))
            except ProgrammingError as e:
                 log.warning(f"Could not drop alembic_version (might be okay): {e}")


        # --- Run Migrations ---

        try:
            # Ensure env.py uses Base.metadata and does NOT import models
            command.upgrade(alembic_cfg, "head")
        except Exception as e:
             # Catch specific errors if needed, otherwise fail broadly
             log.exception("!!! Alembic upgrade command failed !!!")
             pytest.fail(f"Alembic upgrade failed: {e}")


        yield sync_engine # Provide engine mainly for dependency ordering

    finally:
        # --- Post-Session Teardown ---

        if sync_engine:
            try:
                with sync_engine.begin() as conn:
                     Base.metadata.drop_all(bind=conn)

            except Exception as e:
                log.error(f"Error during post-session table drop: {e}", exc_info=True)
            finally:

                 sync_engine.dispose()
        else:
            log.warning("Sync engine not available for teardown.")



# --- Async Engine Fixture ---

@pytest_asyncio.fixture(scope="session")
async def async_engine_test(
    async_test_db_url: str, # Get the resolved async test URL
    db_setup_and_migration: SyncEngine # Depend on the setup fixture
) -> AsyncGenerator[AsyncEngine, None]:
    """ Provides a session-scoped async engine connected to the migrated test DB. """
    # db_setup_and_migration ensures migrations are done before this runs

    engine = create_async_engine(async_test_db_url, echo=False, poolclass=NullPool)
    try:
        yield engine
    finally:

        await engine.dispose()


# --- Async Session Fixture ---

@pytest_asyncio.fixture(scope="function")
async def db_session(
    async_engine_test: AsyncEngine,
    request: pytest.FixtureRequest # Optional: for logging test name
) -> AsyncGenerator[AsyncSession, None]:
    """ Provides a function-scoped async session wrapped in a transaction. """
    test_name = request.node.name
    log.debug(f"--- DB_SESSION Start [Test: {test_name}] ---")

    session_factory = async_sessionmaker(
        bind=async_engine_test, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:

        # Start transaction
        await session.begin()

        try:
            # Provide session to test function
            yield session
        finally:
            # Rollback transaction after test function completes

            await session.rollback()

            # Session is closed automatically by the context manager

    log.debug(f"--- DB_SESSION End [Test: {test_name}] ---")
