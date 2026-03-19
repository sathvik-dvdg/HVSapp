# app/api/endpoints/admin.py
import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

# Import project components
from app.api import deps # Contains dependencies: get_db, require_admin_role
from app.db.session import get_db
from app.models.user import User, UserRole # Import User and UserRole enum
from app.schemas.user import UserCreate, UserRead # Import Pydantic schemas
from app.services import user_service # Import the user service

log = logging.getLogger(__name__)

# --- API Router Initialization ---
router = APIRouter()
# ---------------------------------

# --- ENDPOINT 1: CREATE USER BY ADMIN (POST) ---
@router.post(
    "/users", # Path: /api/v1/admin/users
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(deps.require_admin_role)], # Protect with Admin role check
    summary="Admin Create New Staff User"
)
def create_user_by_admin(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate, # Data received from the Admin form
) -> Any:
    """
    Admin endpoint to create a new Doctor or Nurse user.
    """
    log.info(f"Admin request received to create user: {user_in.username} with role: {user_in.role}")

    # Check if user already exists
    existing_user = user_service.get_user_by_username(db, username=user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered.",
        )

    # Prevent Admin from creating another admin via the API (optional safety)
    if user_in.role == UserRole.ADMIN:
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create admin users via this endpoint.",
        )

    # Create the user using the existing service function
    new_user = user_service.create_user(db=db, user_in=user_in)

    if new_user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User could not be created due to an internal error.",
        )

    log.info(f"Admin successfully created user: {new_user.username}")
    return new_user


# --- ENDPOINT 2: LIST USERS (GET) ---
@router.get(
    "/users", # Path: /api/v1/admin/users
    response_model=List[UserRead], # Return a list of users (excluding password)
    dependencies=[Depends(deps.require_admin_role)], # Protect with Admin role check
    summary="List Non-Admin Users",
    description="Admin endpoint to retrieve a paginated list of all Doctor and Nurse users."
)
def list_users(
    *,
    db: Session = Depends(get_db),
    # Add validation for pagination parameters using Query
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of records to return (max 200)"),
) -> Any:
    """
    Admin endpoint to retrieve a list of all Doctor and Nurse users with pagination.
    """
    log.info(f"Admin request received to list users (skip={skip}, limit={limit}).")
    users = user_service.get_all_users(db=db, skip=skip, limit=limit)
    log.info(f"Returning {len(users)} users to admin.")
    return users