
# Database Migration Scripts

This directory contains scripts for managing database migrations.

## run_all_migrations.py

This script runs database migrations for both the development and test databases.

### Usage

```bash
# Run migrations on both development and test databases
python run_all_migrations.py

# Skip test database migrations
python run_all_migrations.py --skip-test-db
```

### How It Works

1. The script first runs migrations on the development database using Alembic.
2. If successful, it then handles the test database in one of two ways:
   - If `--skip-test-db` is specified, it skips test database migrations.
   - Otherwise, it initializes the test database schema using SQLAlchemy's `create_all()` and then runs migrations.

### Error Handling

Any errors during migration are logged to HTML files in the `backend/migration_error_logs` directory.

## setup_test_db.py

This script is used to set up the test database for testing purposes.

### Usage

```bash
# Set up the test database
python setup_test_db.py
```

### How It Works

The script runs Alembic migrations against the test database by temporarily overriding the `MIGRATION_DATABASE_URL` environment variable.