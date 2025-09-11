from __future__ import annotations

import os
from typing import Any

try:
    # Prefer Pydantic v2-compatible settings if available
    from pydantic_settings import BaseSettings
    _HAS_PYDANTIC_SETTINGS = True
except ImportError:  # pragma: no cover
    # Fallback: allow defaults via BaseModel when pydantic-settings isn't installed
    from pydantic import BaseModel as BaseSettings
    _HAS_PYDANTIC_SETTINGS = False


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/app.db"
    LOG_LEVEL: str = "INFO"  # DEBUG/INFO/WARNING/ERROR/CRITICAL
    APP_NAME: str = "Notes API"
    ENV: str = "dev"
    ENABLE_FTS: bool = False  # placeholder, unused


def _env_overrides() -> dict[str, Any]:
    """Minimal env reader when pydantic-settings is unavailable.

    Only reads known fields and performs simple type coercion.
    """
    def _get_bool(name: str, default: bool) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    # Defaults mirror the dataclass defaults above
    defaults: dict[str, Any] = {
        "DATABASE_URL": "sqlite:///./data/app.db",
        "LOG_LEVEL": "INFO",
        "APP_NAME": "Notes API",
        "ENV": "dev",
        "ENABLE_FTS": False,
    }

    overrides: dict[str, Any] = {}
    for key, default in defaults.items():
        if isinstance(default, bool):
            overrides[key] = _get_bool(key, default)
        else:
            overrides[key] = os.getenv(key, default)
    return overrides


def get_settings() -> Settings:
    # If pydantic-settings is available, let it handle env parsing
    if _HAS_PYDANTIC_SETTINGS:
        return Settings()
    # Otherwise, manually read from env
    return Settings(**_env_overrides())


settings = get_settings()

# OpenAPI / API metadata
API_TITLE: str = "Notes API"
API_SUMMARY: str = "Simple notes with tags"
API_VERSION: str = "0.3.0"
API_CONTACT: dict[str, str] = {"name": "Notes Team", "url": "https://example.invalid"}
API_LICENSE: dict[str, str] = {"name": "MIT"}
