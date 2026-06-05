# app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from src.modules.auth.models import UserRole

# --- Base Schema (Common fields) ---
class UserBase(BaseModel):
    username: EmailStr
    full_name: Optional[str] = None
    role: UserRole

# --- Schema for Creating a User ---
class UserCreate(UserBase):
    password: str

# --- Schema for Updating a User ---
class UserUpdate(BaseModel):
    username: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None

# --- Schema for Reading User Data ---
class UserRead(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Schema for Device Token (Task 1.4) ---
class DeviceTokenUpdate(BaseModel):
    device_token: str
