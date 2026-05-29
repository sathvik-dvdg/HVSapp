# create_admin.py
import logging
from sqlalchemy.orm import Session

# --- FIX: EXPLICITLY IMPORT ALL MODELS ---
# This forces SQLAlchemy to register all models before any queries are run.
from src.db.base_class import Base
from src.modules.auth.models import User, UserRole
from src.modules.auth.schemas import UserCreate
from src.modules.auth import service as user_service
from src.modules.patients.models import Patient

# Import other components
from src.db.session import SessionLocal
from src.schemas.user import UserCreate
from src.services import user_service
from src.schemas.user import UserRole 

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- Configure Admin User Details ---
ADMIN_USERNAME = "admin@hospital.com"
ADMIN_PASSWORD = "VerySecureAdminPassword123!"
ADMIN_FULL_NAME = "Hospital Admin"
# --- End Configuration ---

def create_first_admin(db: Session) -> None:
    """Creates the initial admin user if they don't exist."""
    log.info(f"Checking if admin user '{ADMIN_USERNAME}' exists...")
    # This query should now work as all models are registered
    user = user_service.get_user_by_username(db, username=ADMIN_USERNAME)

    if user:
        log.info(f"Admin user '{ADMIN_USERNAME}' already exists. Skipping creation.")
        return

    log.info(f"Admin user '{ADMIN_USERNAME}' not found. Attempting creation...")
    user_in = UserCreate(
        username=ADMIN_USERNAME,
        password=ADMIN_PASSWORD,
        full_name=ADMIN_FULL_NAME,
        role=UserRole.ADMIN
    )
    new_admin = user_service.create_user(db=db, user_in=user_in)

    if new_admin:
        log.info(f"Successfully created admin user: {new_admin.username} (ID: {new_admin.id})")
    else:
        log.error(f"Failed to create admin user: {ADMIN_USERNAME}.")

if __name__ == "__main__":
    log.info("--- Running Admin User Bootstrap Script ---")
    db = SessionLocal()
    try:
        create_first_admin(db)
    except Exception as e:
        log.error(f"An error occurred during admin creation: {e}", exc_info=True)
    finally:
        db.close()
        log.info("--- Admin Bootstrap Script Finished ---")