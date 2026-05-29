# app/core/security.py
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

# Import the settings instance, which loads .env variables
from src.config.config import settings

# --- Password Hashing Setup ---
# We configure passlib to use 'bcrypt' as the default scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- JWT Configuration ---
# Load settings from the config file
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# --- Password Utilities ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a stored hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Log potential errors (e.g., invalid hash format)
        logging.error(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Hashes a plain-text password using bcrypt."""
    return pwd_context.hash(password)

# --- JWT Token Utilities ---
def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a JWT access token.
    'subject' can be the user's ID or username (must be convertible to string).
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # 'sub' (subject) is the standard JWT claim for the user's identity
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """
    Decodes and verifies a JWT token.

    Returns:
        The 'subject' (username) if the token is valid and not expired.
        None if verification fails.
    """
    try:
        # jwt.decode automatically handles expiration ('exp') validation
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Get the 'subject' claim from the token payload
        subject: Optional[str] = payload.get("sub")
        
        if subject is None:
            logging.warning("JWT token verification failed: Missing 'sub' claim.")
            return None
            
        return subject
        
    except jwt.ExpiredSignatureError:
        logging.warning("JWT token verification failed: Token has expired.")
        return None
    except JWTError as e:
        # Catches various JWT format/signature errors
        logging.error(f"JWT token verification failed: Invalid token - {e}")
        return None