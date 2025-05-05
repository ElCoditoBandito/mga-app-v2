#!/usr/bin/env python
# backend/scripts/run_all_migrations.py

import os
import sys
import subprocess
import datetime
import traceback
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to sys.path to allow importing from backend
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)
project_root = os.path.dirname(backend_dir)
sys.path.append(project_root)

# Load environment variables
load_dotenv()

# We'll import models inside the functions where they're needed
# to avoid module-level import issues

def log_error_to_html(step, command, stdout, stderr, error_type=None, traceback_str=None):
    """
    Log migration errors to an HTML file.
    
    Args:
        step (str): The migration step that failed (e.g., "Development DB Migration")
        command (str): The command that was executed
        stdout (str): Standard output from the command
        stderr (str): Standard error from the command
        error_type (str, optional): Type of error if an exception occurred
        traceback_str (str, optional): Traceback information if an exception occurred
    """
    timestamp = datetime.datetime.now()
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    
    # Create the log directory if it doesn't exist
    log_dir = Path(__file__).resolve().parent.parent / "migration_error_logs"
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # Create a unique filename for the error log
    log_file = log_dir / f"migration_error_{timestamp_str}.html"
    
    # Create the HTML content
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>Migration Error Report - {timestamp.strftime("%Y-%m-%d %H:%M:%S")}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #d9534f;
        }}
        .error-section {{
            margin-bottom: 30px;
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 4px;
        }}
        .error-section h3 {{
            margin-top: 0;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .error-output {{
            background-color: #f2dede;
            border-color: #ebccd1;
        }}
        .command {{
            font-family: monospace;
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 4px;
            border-left: 4px solid #5bc0de;
        }}
        .timestamp {{
            color: #777;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <h1>Migration Error Report</h1>
    <p class="timestamp">Generated on {timestamp.strftime("%Y-%m-%d at %H:%M:%S")}</p>
    
    <div class="error-section">
        <h2>Error Summary</h2>
        <p><strong>Failed Step:</strong> {step}</p>
        <p><strong>Command:</strong></p>
        <div class="command">{command}</div>
        
        {f'<p><strong>Error Type:</strong> {error_type}</p>' if error_type else ''}
    </div>
    
    <div class="error-section">
        <h3>Standard Output</h3>
        <pre>{stdout or "No standard output"}</pre>
    </div>
    
    <div class="error-section">
        <h3>Standard Error</h3>
        <pre class="error-output">{stderr or "No standard error"}</pre>
    </div>
    
    {f'''<div class="error-section">
        <h3>Traceback</h3>
        <pre class="error-output">{traceback_str}</pre>
    </div>''' if traceback_str else ''}
</body>
</html>
"""
    
    # Write the HTML content to the file
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Error log saved to: {log_file}")
    return log_file

def run_command(command_list, cwd=None, step_name="Command"):
    """
    Run a command and return the result.
    
    Args:
        command_list (list): The command to run as a list of strings
        cwd (str, optional): The working directory to run the command in
        step_name (str): Name of the step being executed
        
    Returns:
        dict: A dictionary containing the command result information
    """
    command_str = " ".join(command_list)
    print(f"Running: {command_str}")
    
    try:
        # Set up environment variables to ensure Python can find the backend module
        env = os.environ.copy()
        
        # Add both the backend directory and project root to PYTHONPATH
        backend_dir = str(Path(__file__).resolve().parent.parent)
        project_root = str(Path(__file__).resolve().parent.parent.parent)
        
        pythonpath = []
        if "PYTHONPATH" in env and env["PYTHONPATH"]:
            pythonpath.append(env["PYTHONPATH"])
        pythonpath.append(backend_dir)
        pythonpath.append(project_root)
        
        env["PYTHONPATH"] = os.pathsep.join(pythonpath)
        print(f"Setting PYTHONPATH to: {env['PYTHONPATH']}")
            
        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env
        )
        
        # Create a result dictionary with all relevant information
        result_dict = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": command_str,
            "step": step_name,
            "success": result.returncode == 0
        }
        
        if result.returncode == 0:
            print(f"Success: {step_name} completed.")
            if result.stdout.strip():
                print(f"Output:\n{result.stdout}")
        else:
            print(f"ERROR: {step_name} failed with return code {result.returncode}")
            if result.stderr.strip():
                print(f"Error output:\n{result.stderr}")
            
            # Log the error to an HTML file
            log_file = log_error_to_html(
                step=step_name,
                command=command_str,
                stdout=result.stdout,
                stderr=result.stderr
            )
            result_dict["log_file"] = log_file
        
        return result_dict
        
    except Exception as e:
        error_type = type(e).__name__
        traceback_str = traceback.format_exc()
        print(f"ERROR: Exception occurred while running {step_name}: {error_type}: {str(e)}")
        print(traceback_str)
        
        # Log the exception to an HTML file
        log_file = log_error_to_html(
            step=step_name,
            command=command_str,
            stdout="",
            stderr=str(e),
            error_type=error_type,
            traceback_str=traceback_str
        )
        
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(e),
            "command": command_str,
            "step": step_name,
            "success": False,
            "exception": e,
            "traceback": traceback_str,
            "log_file": log_file
        }

def run_dev_db_migration():
    """
    Run migrations on the development database.
    
    Returns:
        dict: The result of the migration command
    """
    backend_dir = Path(__file__).resolve().parent.parent
    alembic_ini_path = backend_dir / "alembic.ini"
    
    return run_command(
        ["alembic", "-c", str(alembic_ini_path), "upgrade", "head"],
        cwd=backend_dir,
        step_name="Development DB Migration"
    )

def run_test_db_migration_with_logging(skip_test_db=False):
    """
    Run migrations on the test database with error logging.
    
    Args:
        skip_test_db (bool): If True, skip test database migrations
        
    Returns:
        dict: The result of the migration
    """
    if skip_test_db:
        print("\n--- Skipping Test DB Migration ---")
        return {
            "returncode": 0,
            "stdout": "Test database migration skipped as requested.",
            "stderr": "",
            "command": "skip_test_db_migration",
            "step": "Test DB Migration",
            "success": True
        }
    print("\n--- Running Migrations on Test DB ---")
    
    # Get the test database URL
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if not test_db_url:
        error_msg = "ERROR: TEST_DATABASE_URL environment variable not set"
        print(error_msg)
        
        # Log the error to an HTML file
        log_file = log_error_to_html(
            step="Test DB Migration",
            command="Setting up test database environment",
            stdout="",
            stderr=error_msg
        )
        
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": error_msg,
            "command": "Setting up test database environment",
            "step": "Test DB Migration",
            "success": False,
            "log_file": log_file
        }
    
    # Store the original migration database URL if it exists
    original_migration_url = os.environ.get("MIGRATION_DATABASE_URL")
    
    try:
        # Override the migration database URL with the test database URL
        os.environ["MIGRATION_DATABASE_URL"] = test_db_url
        print(f"Using test database: {test_db_url}")
        
        # Initialize the test database schema using SQLAlchemy
        print("Initializing test database schema...")
        from sqlalchemy import create_engine
        
        # Import Base and models
        try:
            # Always import Base fresh within this function
            from backend.models.base import Base as ModelBase
            print("Successfully imported Base")
            
            # Import all models to ensure they're registered with Base.metadata
            print("Importing models...")
            import backend.models.user
            import backend.models.club
            import backend.models.membership
            import backend.models.fund
            import backend.models.fund_membership
            import backend.models.portfolio
            import backend.models.asset
            import backend.models.position
            import backend.models.transaction
            import backend.models.income
            import backend.models.performance_snapshot
            print("All models imported successfully")
            
            # Create engine and initialize schema
            print(f"Creating engine with URL: {test_db_url}")
            engine = create_engine(test_db_url)
            
            # Verify Base has metadata
            if not hasattr(ModelBase, 'metadata'):
                print("Error: Base does not have metadata attribute")
                raise AttributeError("Base does not have metadata attribute")
                
            print(f"Base metadata tables: {list(ModelBase.metadata.tables.keys())}")
            ModelBase.metadata.create_all(engine)
            print("Test database schema initialized successfully.")
            
        except ImportError as e:
            print(f"Error importing models: {e}")
            print(f"Current sys.path: {sys.path}")
            raise
        except Exception as e:
            print(f"Error initializing schema: {type(e).__name__}: {str(e)}")
            raise
        
        # Run Alembic migrations
        print("Running migrations on test database...")
        backend_dir = Path(__file__).resolve().parent.parent
        alembic_ini_path = backend_dir / "alembic.ini"
        
        result = run_command(
            ["alembic", "-c", str(alembic_ini_path), "upgrade", "head"],
            cwd=backend_dir,
            step_name="Test DB Migration"
        )
        
        if result["success"]:
            print("Test database migration completed successfully.")
        
        return result
        
    except Exception as e:
        error_type = type(e).__name__
        traceback_str = traceback.format_exc()
        print(f"ERROR: Exception occurred during test database migration: {error_type}: {str(e)}")
        print(traceback_str)
        
        # Log the exception to an HTML file
        log_file = log_error_to_html(
            step="Test DB Migration",
            command="alembic upgrade head (for test database)",
            stdout="",
            stderr=str(e),
            error_type=error_type,
            traceback_str=traceback_str
        )
        
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(e),
            "command": "alembic upgrade head (for test database)",
            "step": "Test DB Migration",
            "success": False,
            "exception": e,
            "traceback": traceback_str,
            "log_file": log_file
        }
        
    finally:
        # Restore the original migration database URL if it existed
        if original_migration_url:
            os.environ["MIGRATION_DATABASE_URL"] = original_migration_url
        else:
            os.environ.pop("MIGRATION_DATABASE_URL", None)

def main():
    """
    Main function to run all migrations.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run database migrations for development and test databases.")
    parser.add_argument("--skip-test-db", action="store_true", help="Skip test database migrations")
    args = parser.parse_args()
    
    print("\n=== Database Migration Tool ===")
    print("This script will run migrations on both development and test databases.")
    print("Any errors will be logged to HTML files in the 'migration_error_logs' directory.")
    if args.skip_test_db:
        print("Note: Test database migrations will be skipped.")
    print("=" * 30)
    
    print("\n--- Running Migrations on Development DB ---")
    dev_result = run_dev_db_migration()
    
    if not dev_result["success"]:
        print("\n--- Development DB Migration Failed. Stopping. ---")
        sys.exit(1)
    
    # If development migration succeeded, run test migration (unless skipped)
    test_result = run_test_db_migration_with_logging(skip_test_db=args.skip_test_db)
    
    if not test_result["success"]:
        print("\n--- Test DB Migration Failed. ---")
        sys.exit(1)
    
    print("\n--- All Migrations Completed Successfully ---")
    return 0

if __name__ == "__main__":
    sys.exit(main())