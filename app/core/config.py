from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PriceTracker"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security / Auth
    SECRET_KEY: str = "supersecret_jwt_key_change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = "sqlite:///./pricetracker.db"
    USE_SQLITE_FALLBACK: bool = True
    SQLITE_DB_PATH: str = "sqlite:///./pricetracker.db"
    
    # Email / SMTP
    SMTP_HOST: Optional[str] = "sandbox.smtp.mailtrap.io"
    SMTP_PORT: int = 2525
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: str = "alerts@pricetracker.local"
    EMAILS_FROM_NAME: str = "PriceTracker Alert"
    ENABLE_EMAIL_ALERTS: bool = False
    
    # Scraper
    SCRAPER_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    )
    SCRAPER_REQUEST_TIMEOUT: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
