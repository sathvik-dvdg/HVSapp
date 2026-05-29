# app/db/session.py
import logging
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.config.config import settings
log = logging.getLogger(__name__)

# Initialize engine variable
engine = None

try:
    # Create the SQLAlchemy engine using the DATABASE_URL
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True  # Checks connection validity before use
    )

    # --- Test Connection ---
    # Try connecting to ensure credentials, host, and port are valid
    with engine.connect() as connection:
        log.info("--- Database engine created and connection successful. ---")

except Exception as e:
    log.critical(f"--- FATAL ERROR: Database engine creation failed: {e} ---")
    log.critical("--- Please check your DATABASE_URL in the .env file and ensure the PostgreSQL server is running. ---")
    sys.exit(f"Database connection failed: {e}") # Exit if DB connection fails on startup


# Create a configured "Session" class
# This is the class that will be used to create individual DB sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
log.info("--- SQLAlchemy SessionLocal created successfully. ---")


def get_db() -> Session:
    """
    FastAPI dependency that provides a SQLAlchemy database session.
    Ensures the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db  # Provide the session to the endpoint function
    finally:
        db.close() # Ensure the session is closed, releasing resources