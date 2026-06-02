import logging
from sqlalchemy import text
from src.db.session import engine
from src.config.security import get_password_hash

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

ADMIN_USERNAME = "admin@hospital.com"
ADMIN_PASSWORD = "VerySecureAdminPassword123!"

def create_first_admin():
    log.info(f"Checking if admin user '{ADMIN_USERNAME}' exists...")
    hashed_pw = get_password_hash(ADMIN_PASSWORD)

    try:
        with engine.begin() as conn:
            # Check if user exists using Raw SQL (Bypasses SQLAlchemy Mapper)
            result = conn.execute(
                text("SELECT id FROM users WHERE username = :username"),
                {"username": ADMIN_USERNAME}
            ).fetchone()

            if result:
                log.info(f"Admin user '{ADMIN_USERNAME}' already exists. Skipping creation.")
                return

            # Insert via raw SQL
            conn.execute(
                text("""
                    INSERT INTO users (username, hashed_password, full_name, role) 
                    VALUES (:username, :password, :full_name, 'admin')
                """),
                {
                    "username": ADMIN_USERNAME,
                    "password": hashed_pw,
                    "full_name": "Hospital Admin"
                }
            )
            log.info(f"Successfully created admin user: {ADMIN_USERNAME}")
    except Exception as e:
        log.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    log.info("--- Running Admin User Bootstrap Script (RAW SQL) ---")
    create_first_admin()
    log.info("--- Admin Bootstrap Script Finished ---")