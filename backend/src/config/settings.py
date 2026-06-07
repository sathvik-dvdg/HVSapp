import json
import logging
from pathlib import Path

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

log = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    GOOGLE_APPLICATION_CREDENTIALS: str
    FIREBASE_CREDENTIALS_PATH: str
    PHI_ENCRYPTION_KEY: str
    CORS_ALLOWED_ORIGINS: list[str] = Field(default_factory=list)
    REDIS_URL: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_allowed_origins(cls, value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []
            if raw_value.startswith("["):
                parsed = json.loads(raw_value)
                if not isinstance(parsed, list):
                    raise ValueError("CORS_ALLOWED_ORIGINS JSON value must be an array")
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
            return [origin.strip() for origin in raw_value.split(",") if origin.strip()]
        raise ValueError("CORS_ALLOWED_ORIGINS must be a list or comma-separated string")

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_access_token_expiry(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
        if value > 30:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES cannot exceed 30")
        return value

    @field_validator("REFRESH_TOKEN_EXPIRE_DAYS")
    @classmethod
    def validate_refresh_token_expiry(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be positive")
        return value


try:
    settings = Settings()
    log.debug("Application settings loaded successfully.")
except ValidationError:
    log.critical("Failed to load application settings from environment.", exc_info=True)
    raise
