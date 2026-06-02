from src.db.session import engine
from sqlalchemy import text

def reset_database():
    with engine.begin() as conn:
        # Drops all tables, types, and enums, then recreates a clean schema
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
    print("Database reset successfully.")

if __name__ == "__main__":
    reset_database()