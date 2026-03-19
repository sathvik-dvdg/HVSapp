# app/api/deps.py
import logging
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import verify_token
from app.models.user import User, UserRole
from app.services import user_service

log = logging.getLogger(__name__)

# This tells FastAPI that the token can be found at the `/api/v1/login/token` endpoint.
# It adds the "Authorize" button to the /docs UI.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login/token")


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to verify the JWT token and return the authenticated user.
    Raises HTTPException 401 if authentication fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Verify the token structure and signature
    username = verify_token(token)
    if username is None:
        log.warning("Token verification failed (invalid token, expired, or missing subject).")
        raise credentials_exception

    # 2. Fetch the user from the database
    user = user_service.get_user_by_username(db, username=username)
    if user is None:
        log.warning(f"Token valid, but user '{username}' not found in DB.")
        raise credentials_exception

    # 3. Return the authenticated user object
    log.debug(f"Authenticated user retrieved: {user.username}")
    return user


def require_admin_role(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency requiring the user making the request to have the 'admin' role.
    Raises HTTPException 403 if the user is not an admin.
    """
    if current_user.role != UserRole.ADMIN:
        log.warning(f"Access denied: User '{current_user.username}' attempted admin action but role is '{current_user.role}'.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires administrator privileges",
        )
    log.debug(f"Admin access granted for user: {current_user.username}")
    return current_user

# You could add other role dependencies here if needed, e.g.:
# def require_doctor_role(...)
# def require_nurse_role(...)