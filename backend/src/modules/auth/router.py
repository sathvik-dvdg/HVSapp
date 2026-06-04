# app/api/endpoints/auth.py
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Import project components
from src.db.session import get_db
from src.modules.auth.schemas import UserCreate, UserRead
from src.modules.auth.token_schema import Token
from src.modules.auth.models import UserRole
from src.modules.auth import service as user_service
from src.config.security import create_access_token
from src.api.dependencies import get_optional_current_user

log = logging.getLogger(__name__)

# Create an API router for authentication endpoints
router = APIRouter()

@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User"
)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: Any = Depends(get_optional_current_user),
) -> Any:
    """
    Create a new user (Doctor or Nurse).
    This is the initial self-registration endpoint.
    """
    log.info(f"Attempting registration for username: {user_in.username}")

    if user_in.role in (UserRole.ADMIN, UserRole.DOCTOR):
        if current_user is None or current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only an existing ADMIN can create ADMIN or DOCTOR accounts."
            )
    
    # Check if user already exists
    user = user_service.get_user_by_username(db, username=user_in.username)
    if user:
        log.warning(f"Registration failed: Username '{user_in.username}' already exists.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered.",
        )
        
    # Create the user
    new_user = user_service.create_user(db=db, user_in=user_in)
    if new_user is None:
        log.error(f"User creation failed for {user_in.username}. Service returned None.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User could not be created due to an internal error.",
        )
        
    log.info(f"Successfully registered user: {new_user.username}")
    return new_user

    
@router.post("/login/token", response_model=Token, summary="Login for Access Token")
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    # Authenticate the user
    user = user_service.authenticate_user(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        log.warning(f"Login failed: Invalid credentials for username '{form_data.username}'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Pass BOTH the username and the string value of the user's role
    access_token = create_access_token(subject=user.username, role=user.role.value)
    
    log.info(f"Login successful for user: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}