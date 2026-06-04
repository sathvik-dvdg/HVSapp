import logging
import traceback
from sqlalchemy import text, inspect
from src.db.session import engine
from src.config.security import get_password_hash
from alembic.config import Config
from alembic import command

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
        print(f"Failed to wipe database: {e}")
        return

    log.info("--- 2. RUNNING MIGRATIONS ---")
    try:
        # Extract the exact database URL without masking the password
        url = engine.url.render_as_string(hide_password=False)
        
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", url.replace('%', '%%'))
        
        command.upgrade(alembic_cfg, "head")
        print("Migrations successfully applied.")
        
        inspector = inspect(engine)
        if 'users' not in inspector.get_table_names():
            print("CRITICAL ERROR: 'users' table is still missing after migration.")
            return
            
    except Exception as e:
        print("\n" + "="*50)
        print("🚨 MIGRATION FAILED 🚨")
        print("="*50)
        traceback.print_exc()
        return

    log.info("--- 3. CREATING ADMIN USER ---")
    try:
        hashed_pw = get_password_hash("VerySecureAdminPassword123!")
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO users (username, hashed_password, full_name, role) 
                    VALUES (:username, :password, :full_name, 'ADMIN')
                """),
                {
                    "username": "admin@hospital.com",
                    "password": hashed_pw,
                    "full_name": "Hospital Admin"
                }
            )
        print("Successfully created admin user: admin@hospital.com")
    except Exception as e:
        print(f"Failed to create admin: {e}")

if __name__ == "__main__":
    run_setup()