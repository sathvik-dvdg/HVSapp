import os
import sys
from pathlib import Path
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import create_engine
from sqlalchemy import pool
from alembic import context

backend_root = Path(__file__).resolve().parents[1]
load_dotenv(backend_root / ".env")

# Ensure the root backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.db.base_class import Base
# Import all models so Alembic autogenerate detects them
from src.modules.auth.models import User
from src.modules.patients.models import Patient
from src.modules.patients.encounter_models import Encounter

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    db_url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    connectable = create_engine(db_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()