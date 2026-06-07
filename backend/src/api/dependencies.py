# backend/src/api/dependencies.py
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.config.settings import settings
from src.config.security import decode_access_token
from src.modules.auth.models import User, UserRole
from src.modules.auth import service as auth_service

log = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Secure dependency to verify the JWT token without querying the database.
    It reads the user ID and Role directly from the signed payload.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        log.warning("JWT verification failed during current user lookup.")
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    role: Optional[str] = payload.get("role")
    if user_id is None or role is None:
        log.warning("JWT token missing 'sub' or 'role' claims.")
        raise credentials_exception

    try:
        user = auth_service.get_user_by_id(db, user_id=int(user_id))
        if user is None or not user.is_active:
            log.warning("Active user not found for authenticated token subject %s.", user_id)
            raise credentials_exception
        if user.role != UserRole(role):
            log.warning("JWT role mismatch for user %s. Token role=%s db role=%s.", user_id, role, user.role.value)
        return user
    except ValueError as e:
        log.error(f"JWT verification failed: {e}")
        raise credentials_exception


def get_optional_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme_optional),
) -> Optional[User]:
    if token is None:
        return None
    try:
        return get_current_user(db=db, token=token)
    except HTTPException:
        return None


def require_admin_role(current_user: User = Depends(get_current_user)) -> User:
    """Dependency requiring the user to have the 'admin' role."""
    if current_user.role != UserRole.ADMIN:
        log.warning(f"Access denied: User {current_user.id} attempted admin action.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires administrator privileges",
        )
    return current_user
