# app/core/config.py
import logging
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Explicitly load the .env file from the project root
# (assuming this file is at app/core/config.py and .env is at backend/.env)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

log = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    Provides default values primarily for documentation purposes;
    actual values should be set in the environment/.env.
    """
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@host/db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 120))

    class Config:
        # env_file = ".env" # pydantic-settings handles this automatically if python-dotenv is installed
        env_file_encoding = 'utf-8'

try:
    settings = Settings()
    log.debug("Settings loaded successfully.")
except Exception as e:
    log.critical(f"FATAL ERROR: Could not load settings. Check .env file. Error: {e}", exc_info=True)
    raise

# Final check
if 'settings' not in globals():
     raise ImportError("Could not initialize 'settings' object in config.py")