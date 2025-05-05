"""
Diagnostic script to trace import behavior and metadata population.
Run this with: python -m backend.debug_imports
"""
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(name)s:%(lineno)d - %(message)s'
)
log = logging.getLogger(__name__)

log.info("=== Starting Import Diagnostic ===")

# First, import Base and check its state
log.info("Importing Base from backend.core.database...")
from backend.core.database import Base
log.info(f"Base imported. Metadata ID: {id(Base.metadata)}")
log.info(f"Tables in Base.metadata after importing Base: {Base.metadata.tables.keys()}")

# Now import a model directly and see what happens
log.info("\nImporting User model directly...")
from backend.models.user import User
log.info(f"User model imported. Metadata ID: {id(Base.metadata)}")
log.info(f"Tables in Base.metadata after importing User: {Base.metadata.tables.keys()}")

# Now import from models.enums (which is imported in the migration)
log.info("\nImporting Currency from backend.models.enums...")
from backend.models.enums import Currency
log.info(f"Currency enum imported. Metadata ID: {id(Base.metadata)}")
log.info(f"Tables in Base.metadata after importing Currency: {Base.metadata.tables.keys()}")

# Now import all models through models.__init__
log.info("\nImporting all models through models.__init__...")
import backend.models
log.info(f"All models imported. Metadata ID: {id(Base.metadata)}")
log.info(f"Tables in Base.metadata after importing all models: {Base.metadata.tables.keys()}")

# Let's check what happens if we try to import the models again
log.info("\nTrying to import User model again...")
try:
    # This should not redefine the table
    from backend.models.user import User
    log.info("User model imported again without error")
except Exception as e:
    log.error(f"Error importing User model again: {e}")

log.info(f"Tables in Base.metadata after re-importing User: {Base.metadata.tables.keys()}")

# Let's check what happens in the migration environment
log.info("\nSimulating migration environment...")
log.info("First, let's import Base in a new variable to see if it's the same instance")
from backend.core.database import Base as Base2
log.info(f"Base2 imported. Metadata ID: {id(Base2.metadata)}")
log.info(f"Are Base and Base2 the same? {Base is Base2}")
log.info(f"Are their metadata objects the same? {Base.metadata is Base2.metadata}")

log.info("\n=== Import Diagnostic Complete ===")