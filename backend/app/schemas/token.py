# app/schemas/token.py
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """
    Schema for the JWT access token response sent to the client upon login.
    """
    access_token: str
    token_type: str = "bearer" # Standard token type

class TokenData(BaseModel):
    """
    Schema representing the data payload decoded from a valid JWT.
    Contains the subject (e.g., username/ID).
    """
    username: Optional[str] = None