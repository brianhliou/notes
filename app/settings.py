try:
    # Prefer Pydantic v2-compatible settings if available
    from pydantic_settings import BaseSettings  # type: ignore
except Exception:  # pragma: no cover
    # Fallback: allow defaults via BaseModel when pydantic-settings isn't installed
    from pydantic import BaseModel as BaseSettings  # type: ignore


class Settings(BaseSettings):
    APP_NAME: str = "notes-api"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite:///./data/app.db"


settings = Settings()

