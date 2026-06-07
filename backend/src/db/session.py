# app/db/session.py
import logging
import sys
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from src.config.settings import settings

log = logging.getLogger(__name__)

# Initialize engine variable
engine = None

try:
    # Create the SQLAlchemy engine using the DATABASE_URL with hardened pool settings
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=30,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=False,
    )

    # Enforce connection timeout at the PostgreSQL level
    @event.listens_for(engine, "connect")
    def set_pg_timeout(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("SET statement_timeout = '30s'")  # kill runaway queries
        cursor.close()

    # --- Test Connection ---
    with engine.connect() as connection:
        log.info("--- Database engine created and connection successful. ---")

except Exception as e:
    log.critical(f"--- FATAL ERROR: Database engine creation failed: {e} ---")
    log.critical("--- Please check your DATABASE_URL in the .env file and ensure the PostgreSQL server is running. ---")
    sys.exit(f"Database connection failed: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
log.info("--- SQLAlchemy SessionLocal created successfully. ---")

def get_db() -> Session:
    """
    FastAPI dependency that provides a SQLAlchemy database session.
    Ensures the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
