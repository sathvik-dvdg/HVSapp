# app/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import project components
from app.db.session import engine # Import the configured DB engine
from app.core.config import settings # Import settings (though not directly used here, good practice)

# Import all the routers
from app.api.endpoints import auth
from app.api.endpoints import admin
from app.api.endpoints import patients
from app.api.endpoints import encounters
from app.api.endpoints import tasks
from app.api.endpoints import handoff # WebSocket router

# Configure logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    Connects to the database on startup, disposes on shutdown.
    """
    log.info("--- HVS Application Startup ---")
    log.info("Attempting database connection...")
    try:
        # Test database connection on startup
        with engine.connect() as connection:
            log.info("--- Database connection successful during startup! ---")
    except Exception as e:
        log.critical(f"--- FATAL: Database connection failed during startup: {e} ---")
        # In a production env, you might want to raise SystemExit(e)
    
    yield # The application is now running

    log.info("--- HVS Application Shutdown ---")
    engine.dispose() # Cleanly close all database connections in the pool


# --- FastAPI App Initialization ---
app = FastAPI(
    title="HVS Clinical Workflow Backend",
    description="API for the Hand-Off Validation System, managing patients, encounters, tasks, and real-time dictation.",
    version="1.0.0",
    lifespan=lifespan # Attach the startup/shutdown handler
)

# --- CORS Middleware ---
# Allows your React Native frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (e.g., localhost, your app)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PATCH, etc.)
    allow_headers=["*"],  # Allows all headers
)


# --- Include All API Routers ---
log.info("Including API routers...")

# Authentication routes (e.g., /api/v1/login/token)
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])

# Admin routes (e.g., /api/v1/admin/users)
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

# Patient routes (e.g., /api/v1/patients/register)
app.include_router(patients.router, prefix="/api/v1/patients", tags=["Patients"])

# Encounter routes (e.g., /api/v1/encounters/{id})
app.include_router(encounters.router, prefix="/api/v1/encounters", tags=["Encounters"])

# Task routes (e.g., /api/v1/tasks/me)
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])

# WebSocket router (e.g., /ws/dictation/{id})
app.include_router(handoff.router, tags=["Real-Time Dictation"])

log.info("Routers included successfully.")

# --- Root Endpoint (Health Check) ---
@app.get("/", tags=["Root"])
def read_root():
    """Provides a simple health check endpoint."""
    return {"Status": "HVS Backend is running!"}


# --- Direct Run Block (for development) ---
if __name__ == "__main__":
    import uvicorn
    # Use 'uvicorn app.main:app --reload' from terminal for full features
    log.info("Starting server directly (for development only)...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)