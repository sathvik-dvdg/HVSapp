# backend/src/api/dependencies.py
import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from src.db.session import get_db
from src.config.config import settings
from src.modules.auth.models import User, UserRole

log = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/token")

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Secure dependency to verify the JWT token without querying the database.
    It reads the user ID and Role directly from the signed payload.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        user_id: Optional[str] = payload.get("sub")
        role: Optional[str] = payload.get("role")
        
        if user_id is None or role is None:
            log.warning("JWT token missing 'sub' or 'role' claims.")
            raise credentials_exception
            
        # We instantiate a dummy User object with just the ID and Role for RBAC checks.
        # This saves a database trip on every single request.
        return User(id=int(user_id), role=UserRole(role))
        
    except (JWTError, ValueError) as e:
        log.error(f"JWT verification failed: {e}")
        raise credentials_exception

def require_admin_role(current_user: User = Depends(get_current_user)) -> User:
    """Dependency requiring the user to have the 'admin' role."""
    if current_user.role != UserRole.ADMIN:
        log.warning(f"Access denied: User {current_user.id} attempted admin action.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires administrator privileges",
        )
    return current_user