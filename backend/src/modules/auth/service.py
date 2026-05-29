# app/services/user_service.py
import logging
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc

# Import project components
from src.config.security import get_password_hash, verify_password
from src.modules.auth.models import User, UserRole
from src.modules.auth.schemas import UserCreate
log = logging.getLogger(__name__)

# --- User Retrieval ---

def get_user_by_username(db: Session, *, username: str) -> Optional[User]:
    """
    Fetch a single user from the database by their username (email).
    """
    log.debug(f"Querying for user with username: {username}")
    return db.query(User).filter(User.username == username).first()

def get_all_users(db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Retrieves a paginated list of all non-admin users (Doctors and Nurses).
    """
    log.info("Querying for all non-admin users.")
    users = (
        db.query(User)
        .filter(User.role != UserRole.ADMIN) # Exclude admins from the list
        .order_by(desc(User.created_at)) # Show newest users first
        .offset(skip)
        .limit(limit)
        .all()
    )
    log.info(f"Retrieved {len(users)} non-admin users.")
    return users

# --- User Creation & Authentication ---

def create_user(db: Session, *, user_in: UserCreate) -> Optional[User]:
    """
    Create a new user in the database after hashing their password.
    """
    log.info(f"Attempting to create user: {user_in.username}")
    try:
        # Hash the password securely before storing
        hashed_password = get_password_hash(user_in.password)

        # Create the SQLAlchemy User model instance
        db_user = User(
            username=user_in.username,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user) # Get ID and defaults assigned by the DB
        log.info(f"Successfully created user in DB: {db_user.username} (ID: {db_user.id})")
        return db_user

    except SQLAlchemyError as e:
        log.error(f"Database error during user creation for {user_in.username}: {e}", exc_info=True)
        db.rollback() # Roll back the transaction on error
        return None
    except Exception as e:
        log.error(f"Unexpected error during user creation for {user_in.username}: {e}", exc_info=True)
        db.rollback()
        return None

def authenticate_user(db: Session, *, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user based on username (email) and password.
    """
    log.debug(f"Authenticating user: {username}")
    user = get_user_by_username(db, username=username)

    # Check if user exists
    if not user:
        log.warning(f"Authentication failed: User '{username}' not found.")
        return None

    # Verify the provided password against the stored hash
    if not verify_password(password, user.hashed_password):
        log.warning(f"Authentication failed: Incorrect password for user '{username}'.")
        return None

    # Authentication successful
    log.info(f"Authentication successful for user: {username}")
    return user