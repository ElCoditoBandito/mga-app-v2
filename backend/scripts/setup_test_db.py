#!/usr/bin/env python
# backend/scripts/setup_test_db.py

import os
import sys
import subprocess
from dotenv import load_dotenv

# Add the parent directory to sys.path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def run_migrations_on_test_db():
    """
    Run Alembic migrations against the test database by temporarily
    overriding the MIGRATION_DATABASE_URL environment variable.
    """
    print("Setting up test database...")
    
    # Get the test database URL
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if not test_db_url:
        print("ERROR: TEST_DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Store the original migration database URL if it exists
    original_migration_url = os.environ.get("MIGRATION_DATABASE_URL")
    
    try:
        # Override the migration database URL with the test database URL
        os.environ["MIGRATION_DATABASE_URL"] = test_db_url
        print(f"Using test database: {test_db_url}")
        
        # Run Alembic migrations
        print("Running migrations...")
        alembic_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alembic.ini")
        result = subprocess.run(
            ["alembic", "-c", alembic_path, "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Migration failed: {result.stderr}")
            sys.exit(1)
        else:
            print(f"Migration successful: {result.stdout}")
            
    finally:
        # Restore the original migration database URL if it existed
        if original_migration_url:
            os.environ["MIGRATION_DATABASE_URL"] = original_migration_url
        else:
            os.environ.pop("MIGRATION_DATABASE_URL", None)
    
    print("Test database setup complete.")

if __name__ == "__main__":
    run_migrations_on_test_db()