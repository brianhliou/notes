try:
    # Prefer Pydantic v2-compatible settings if available
    from pydantic_settings import BaseSettings
except ImportError:  # pragma: no cover
    # Fallback: allow defaults via BaseModel when pydantic-settings isn't installed
    from pydantic import BaseModel as BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "notes-api"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite:///./data/app.db"


settings = Settings()

# OpenAPI / API metadata
API_TITLE: str = "Notes API"
API_SUMMARY: str = "Simple notes with tags"
API_VERSION: str = "0.3.0"
API_CONTACT: dict[str, str] = {"name": "Notes Team", "url": "https://example.invalid"}
API_LICENSE: dict[str, str] = {"name": "MIT"}
