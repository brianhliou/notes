from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import create_engine

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


def db_ready() -> bool:
    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
