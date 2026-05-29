# app/db/base_class.py
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Optional: Define standard naming conventions for database constraints
# This makes your database index and key names consistent.
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)

class Base(DeclarativeBase):
    """
    The base class for all SQLAlchemy models in the application.
    It includes shared metadata and naming conventions.
    """
    metadata = metadata