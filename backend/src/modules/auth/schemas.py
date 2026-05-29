# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Import the UserRole enum from the model file
from src.modules.auth.models import UserRole

# --- Base Schema (Common fields) ---
class UserBase(BaseModel):
    """Base Pydantic model for User, defines common fields."""
    username: EmailStr  # Use EmailStr for built-in email validation
    full_name: Optional[str] = None
    role: UserRole

# --- Schema for Creating a User (receives password) ---
class UserCreate(UserBase):
    """Pydantic model for creating a new user (receives a plain-text password)."""
    password: str

# --- Schema for Updating a User (all fields optional) ---
class UserUpdate(BaseModel):
    """Pydantic model for updating an existing user (all fields optional)."""
    username: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None  # Allow password update
    role: Optional[UserRole] = None

# --- Schema for Reading User Data (excludes password) ---
class UserRead(UserBase):
    """
    Pydantic model for reading user data (sent back to the client).
    It inherits from UserBase and adds fields that are safe to show.
    """
    id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode (SQLAlchemy -> Pydantic)