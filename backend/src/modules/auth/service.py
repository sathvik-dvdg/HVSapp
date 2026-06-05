# app/services/user_service.py
import logging
from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc

from src.config.security import get_password_hash, verify_password
from src.modules.auth.models import User, UserRole
from src.modules.auth.schemas import UserCreate

log = logging.getLogger(__name__)

def get_user_by_username(db: Session, *, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_all_users(db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
    return (
        db.query(User)
        .filter(User.role != UserRole.ADMIN)
        .order_by(desc(User.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_user_by_id(db: Session, *, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, *, user_in: UserCreate) -> Optional[User]:
    try:
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            username=user_in.username,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except SQLAlchemyError as e:
        db.rollback()
        return None
    except Exception as e:
        db.rollback()
        return None

def authenticate_user(db: Session, *, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def update_user_refresh_token(db: Session, user: User, refresh_token: str | None):
    if refresh_token:
        user.refresh_token = get_password_hash(refresh_token)
    else:
        user.refresh_token = None
    db.commit()

def verify_user_refresh_token(user: User, refresh_token: str) -> bool:
    if not user.refresh_token:
        return False
    return verify_password(refresh_token, user.refresh_token)

def update_device_token(db: Session, user: User, device_token: str):
    """Updates the FCM device token for push notifications."""
    user.device_token = device_token
    db.commit()
