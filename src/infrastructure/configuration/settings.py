"""Configuration management with appsettings.json and environment variables"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field

class AppSettings(BaseSettings):
    """Application settings that can be overridden by environment variables"""
    
    # Database
    DATABASE_URL: str = Field(default="")
    DATABASE_HOST: str = Field(default="")
    DATABASE_PORT: int = Field(default=0)
    DATABASE_NAME: str = Field(default="")
    DATABASE_USER: str = Field(default="")
    DATABASE_PASSWORD: str = Field(default="")
    DATABASE_POOL_SIZE: int = Field(default=0)
    DATABASE_MAX_OVERFLOW: int = Field(default=0)
    DATABASE_POOL_RECYCLE: int = Field(default=0)
    DATABASE_POOL_PRE_PING: bool = Field(default=False)
    DATABASE_ECHO: bool = Field(default=False)
    
    # Security
    SECRET_KEY: str = Field(default="")
    JWT_ALGORITHM: str = Field(default="")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=0)
    MAX_REQUEST_SIZE_MB: int = Field(default=10)
    
    # App configuration
    APP_NAME: str = Field(default="ConectaCEU")
    APP_VERSION: str = Field(default="0.1.0")
    APP_FRONTEND_URL: str = Field(default="")
    ENVIRONMENT: str = Field(default="Development")
    
    # CORS
    ALLOWED_ORIGINS: list[str] = Field(default=["http://localhost:3000", "http://localhost:8000"])
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = Field(default=10)
    MAX_PAGE_SIZE: int = Field(default=50)

    # Email Configuration
    EMAIL_SMTP_HOST: str = Field(default="")
    EMAIL_SMTP_PORT: int = Field(default=0)
    EMAIL_SMTP_USER: str = Field(default="")
    EMAIL_SMTP_PASSWORD: str = Field(default="")
    EMAIL_FROM_EMAIL: str = Field(default="")
    EMAIL_FROM_NAME: str = Field(default="")

    # SMS Configuration
    SMS_API_URL: str = Field(default="")
    SMS_API_KEY: str = Field(default="")
    SMS_FROM_NUMBER: str = Field(default="")

    # WhatsApp Configuration
    WHATSAPP_API_URL: str = Field(default="")
    WHATSAPP_PHONE_NUMBER: str = Field(default="")
    WHATSAPP_ACCESS_TOKEN: str = Field(default="")
    WHATSAPP_FROM_NUMBER: str = Field(default="")
    
    BATCH_SIZE: int = Field(default=25)

    # Student deactivation base on unjustified absences
    ABSENCE_DAYS: int = Field(default=7)
    MIN_CONSECUTIVE_UNJUSTIFIED: int = Field(default=3)

    # Deactivated profiles exclusion
    EXCLUSION_HOURS: int = Field(default=168) # one week
    
    # Enrollment
    ENROLLMENT_MONTHS: list[int] = Field(default=[])
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

# Singleton instance
settings = AppSettings()
