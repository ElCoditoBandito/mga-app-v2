# backend/main.py
import os
# from pathlib import Path
# from dotenv import load_dotenv
# load_dotenv()

import logging
import logging.config # For potential file config later
from fastapi import FastAPI
from contextlib import asynccontextmanager # For lifespan events

# --- Core Imports ---
# Import the session initializer
from backend.core.session import initialize_database, async_engine, SessionFactory

# --- API Router ---
# Import the main router that includes all versioned endpoints
from backend.api import api_router

# --- Logging Configuration ---
# Basic config (can be replaced with file config)
logging.basicConfig(
    level=logging.DEBUG, # Adjust level as needed (DEBUG, INFO, WARNING, ERROR)
    format='%(asctime)s %(levelname)-8s %(name)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Example: Set specific log levels for libraries
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING) # Quieter SQL logs
logging.getLogger('uvicorn.access').setLevel(logging.WARNING) # Quieter access logs

log = logging.getLogger(__name__)

# --- Lifespan Management (Startup/Shutdown) ---
# Replaces deprecated @app.on_event("startup") / @app.on_event("shutdown")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    log.info("Application startup...")
    log.info("Initializing database connection...")
    initialize_database() # Initialize engine and session factory
    yield
    # Code to run on shutdown
    log.info("Application shutdown...")
    if async_engine:
        log.info("Disposing database engine...")
        await async_engine.dispose()
    log.info("Shutdown complete.")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Social Investment Club API", # Updated Title
    version="0.1.0",
    description="API for managing social investment clubs, members, transactions, and unit value accounting.",
    lifespan=lifespan # Use the lifespan context manager
)

# --- Include API Routers ---
API_V1_PREFIX = "/api/v1" # Define prefix for v1
app.include_router(api_router, prefix=API_V1_PREFIX)
log.info(f"Included API router with prefix: {API_V1_PREFIX}")

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """ Simple root endpoint to confirm the API is running. """
    return {"message": "Welcome to the Social Investment Club API!"}

# --- Add other middleware, exception handlers, etc. below if needed ---
# CORS Middleware to allow frontend to communicate with the API
from fastapi.middleware.cors import CORSMiddleware
origins = [
    "http://localhost",
    "http://localhost:3000",  # React default dev server
    "http://localhost:5173",  # Vite default dev server
    # Add your deployed frontend URL here when ready
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Removed model_rebuild calls ---
# Pydantic v2 generally handles ForwardRefs automatically during validation/serialization.
# Explicit rebuilds are usually not necessary if schemas are structured correctly.

