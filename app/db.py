from __future__ import annotations

import os
from typing import Iterator

from sqlmodel import SQLModel, create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.settings import settings


# Ensure the SQLite directory exists; does not trigger a DB connection
os.makedirs("./data", exist_ok=True)

# Create a lazy SQLAlchemy engine via SQLModel
engine = create_engine(settings.DATABASE_URL)

# Session factory configured per FastAPI best practices
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a DB session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

