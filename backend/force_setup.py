import logging
import subprocess
import sys
from sqlalchemy import text
from src.db.session import engine
from src.config.security import get_password_hash

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def run_setup():
    log.info("--- 1. WIPING DATABASE ---")
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        log.info("Database wiped clean successfully.")
    except Exception as e:
        log.error(f"Failed to wipe database: {e}")
        return

    log.info("--- 2. RUNNING MIGRATIONS ---")
    try:
        # We use subprocess to force Alembic to run exactly as it would in the terminal
        # and capture any hidden errors. Note: 'alembic.config' is the correct module.
        log.info("Executing Alembic upgrade...")
        result = subprocess.run(
            [sys.executable, "-m", "alembic.config", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            log.error("--- MIGRATION FAILED! ---")
            log.error(f"STDOUT:\n{result.stdout}")
            log.error(f"STDERR:\n{result.stderr}")
            return
            
        log.info("Migrations successfully applied.")
    except Exception as e:
        log.error(f"Failed to run migrations subprocess: {e}")
        return

    log.info("--- 3. CREATING ADMIN USER ---")
    try:
        hashed_pw = get_password_hash("VerySecureAdminPassword123!")
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO users (username, hashed_password, full_name, role) 
                    VALUES (:username, :password, :full_name, 'admin')
                """),
                {
                    "username": "admin@hospital.com",
                    "password": hashed_pw,
                    "full_name": "Hospital Admin"
                }
            )
        log.info("Successfully created admin user: admin@hospital.com")
    except Exception as e:
        log.error(f"Failed to create admin: {e}")

if __name__ == "__main__":
    run_setup()