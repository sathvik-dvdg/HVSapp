# app/api/endpoints/auth.py
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.modules.auth.schemas import UserCreate, UserRead, DeviceTokenUpdate
from src.modules.auth.token_schema import Token, RefreshTokenRequest
from src.modules.auth.models import UserRole
from src.modules.auth import service as user_service
from src.config.security import create_access_token, create_refresh_token, decode_access_token
from src.api.dependencies import get_optional_current_user, get_current_user

log = logging.getLogger(__name__)
router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: Any = Depends(get_optional_current_user),
) -> Any:
    if user_in.role in (UserRole.ADMIN, UserRole.DOCTOR):
        if current_user is None or current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only an existing ADMIN can create ADMIN or DOCTOR accounts."
            )
    
    user = user_service.get_user_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered.")
        
    new_user = user_service.create_user(db=db, user_in=user_in)
    if new_user is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User could not be created.")
        
    return new_user

@router.post("/auth/token", response_model=Token, summary="Login for Access and Refresh Tokens")
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = user_service.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    refresh_token = create_refresh_token(subject=str(user.id))
    user_service.update_user_refresh_token(db, user, refresh_token)
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/auth/refresh", response_model=Token, summary="Refresh JWT using refresh token")
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> Any:
    payload = decode_access_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    user_id_str = payload.get("sub")
    if not user_id_str or not user_id_str.isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    
    user = user_service.get_user_by_id(db, user_id=int(user_id_str))
    if not user or not user_service.verify_user_refresh_token(user, request.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
        
    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    new_refresh_token = create_refresh_token(subject=str(user.id))
    user_service.update_user_refresh_token(db, user, new_refresh_token)
    
    return {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}

@router.post("/auth/logout", summary="Invalidate refresh token")
def logout(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    user = user_service.get_user_by_id(db, user_id=current_user.id)
    if user and user_service.verify_user_refresh_token(user, request.refresh_token):
        user_service.update_user_refresh_token(db, user, None)
    return {"status": "Logged out successfully"}

@router.put("/auth/device-token", summary="Register FCM device token")
def register_device_token(
    request: DeviceTokenUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
) -> Any:
    user = user_service.get_user_by_id(db, user_id=current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    user_service.update_device_token(db, user, request.device_token)
    return {"status": "Device token updated successfully"}
