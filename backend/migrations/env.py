# backend/migrations/env.py

import logging
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Path Setup ---
# Add the 'backend' directory to sys.path to allow importing from core, models etc.
# Assumes env.py is in backend/migrations/
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# --- Import Application's Base ---
# This is crucial for Alembic to know the target schema defined by your models.
# It assumes all your models are imported somewhere when Base is defined or used,
# # so Base.metadata is populated correctly ONCE during initial application/test load.
# try:
#     from backend.core.database import Base
# except ImportError as e:
#     print(f"Error importing Base from backend.core.database: {e}")
#     print("Ensure backend directory is in sys.path and core/database.py exists.")
#     sys.exit(1) # Exit if Base cannot be imported

# --- Alembic Configuration ---
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Target Metadata ---
# Set the target metadata for 'autogenerate' support and migration context.
# This should be the metadata object associated with your application's Base.
# target_metadata = Base.metadata

# --- Migration Functions ---

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable here as well.
    By skipping the Engine creation we don't even need a DBAPI to be
    available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    try:
        from backend.core.database import Base
        import backend.models
    except ImportError as e:
        print(f"Error importing Base from backend.core.database: {e}")
        print("Ensure backend directory is in sys.path and core/database.py exists.")
        sys.exit(1) # Exit if Base cannot be imported
    
    target_metadata = Base.metadata
    # Get the URL from the Alembic config (set by alembic.ini or conftest.py)
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True, # Render SQL statements directly without parameters
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Create engine using configuration from alembic.ini or overridden by conftest.py
    # The 'sqlalchemy.url' should point to the correct database (dev or test).

    try:
        from backend.core.database import Base
        import backend.models
    except ImportError as e:
        print(f"Error importing Base from backend.core.database: {e}")
        print("Ensure backend directory is in sys.path and core/database.py exists.")
        sys.exit(1) # Exit if Base cannot be imported
    
    target_metadata = Base.metadata

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool, # Use NullPool for migration operations
        # url=config.get_main_option("sqlalchemy.url") # engine_from_config reads this
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata # Use the application's Base.metadata
        )

        with context.begin_transaction():
            context.run_migrations()

# --- Main Execution Logic ---
if context.is_offline_mode():
    print("Running migrations offline...")
    run_migrations_offline()
else:
    print("Running migrations online...")
    run_migrations_online()

