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
