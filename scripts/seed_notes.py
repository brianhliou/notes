from __future__ import annotations

import argparse
import os
import random
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Sequence

from sqlalchemy import text, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, create_engine


def resolve_db_url(cli_db_url: str | None) -> str:
    env_url = os.getenv("DATABASE_URL")
    default_url = "sqlite:///./data/app.db"
    return cli_db_url or env_url or default_url


def ensure_sqlite_dir(db_url: str) -> None:
    if not db_url.startswith("sqlite"):
        return
    if ":memory:" in db_url:
        return
    prefix = "sqlite:///"
    path = db_url[len(prefix) :] if db_url.startswith(prefix) else db_url
    # Normalize possible four-slash absolute path e.g. sqlite:////abs/path
    if path.startswith("/") and db_url.startswith("sqlite:////"):
        path = path
    folder = Path(path).resolve().parent
    folder.mkdir(parents=True, exist_ok=True)


def build_engine(db_url: str, allow_app_engine: bool) -> Engine:
    if allow_app_engine:
        try:
            # Try to reuse application engine if no override was provided
            from app.db import engine as app_engine

            return app_engine
        except Exception:
            pass

    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, echo=False, connect_args=connect_args)


def ensure_schema(engine: Engine, db_url: str) -> None:
    insp = inspect(engine)
    if insp.has_table("notes"):
        return  # already good

    # Try Alembic against the SAME DB
    try:
        env = os.environ.copy()
        env["DATABASE_URL"] = db_url
        repo_root = pathlib.Path(__file__).resolve().parents[1]  # project root
        subprocess.run(["alembic", "upgrade", "head"], check=True, cwd=str(repo_root), env=env)
    except Exception:
        pass

    # If still missing, fall back to create_all on this engine
    if not inspect(engine).has_table("notes"):
        from app import models as _models  # ensure models registered
        SQLModel.metadata.create_all(engine)

    # Final guard
    if not inspect(engine).has_table("notes"):
        raise RuntimeError(f"'notes' table still missing for {db_url}")


def reset_notes(session: Session) -> int:
    # Get count first for a better summary
    try:
        count = session.execute(text("SELECT COUNT(*) FROM notes")).scalar_one()
    except Exception:
        count = 0
    session.execute(text("DELETE FROM notes"))
    session.commit()
    return int(count or 0)


WORDS = [
    "alpha",
    "bravo",
    "charlie",
    "delta",
    "echo",
    "foxtrot",
    "golf",
    "hotel",
    "india",
    "juliet",
    "kilo",
    "lima",
    "mike",
    "november",
    "oscar",
    "papa",
    "quebec",
    "romeo",
    "sierra",
    "tango",
    "uniform",
    "victor",
    "whiskey",
    "xray",
    "yankee",
    "zulu",
    "cloud",
    "system",
    "design",
    "pattern",
    "service",
    "note",
    "feature",
    "bug",
    "release",
    "idea",
    "draft",
    "project",
    "reading",
]

TAGS_POOL = [
    "work",
    "personal",
    "ideas",
    "todo",
    "research",
    "draft",
    "inbox",
    "reading",
    "project",
    "journal",
]


def rand_words(n: int) -> list[str]:
    return random.sample(WORDS, k=min(n, len(WORDS)))


def gen_title() -> str:
    parts = rand_words(random.randint(3, 8))
    title = " ".join(w.capitalize() for w in parts)
    if len(title) > 100:
        title = title[:100].rstrip()
    return title


def gen_sentence() -> str:
    n = random.randint(12, 20)
    words = random.choices(WORDS, k=n)
    words[0] = words[0].capitalize()
    return " ".join(words) + "."


def gen_content() -> str:
    s_count = random.randint(2, 4)
    return " ".join(gen_sentence() for _ in range(s_count))


def gen_tags() -> list[str]:
    k = random.randint(0, 3)
    return random.sample(TAGS_POOL, k=k)


def rand_datetimes(days_back: int) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    back_days = random.randint(0, max(0, days_back))
    back_seconds = random.randint(0, 86400)
    created = now - timedelta(days=back_days, seconds=back_seconds)
    if random.random() < 0.5:
        updated = created
    else:
        delta_sec = int((now - created).total_seconds())
        updated = created + timedelta(seconds=random.randint(0, max(0, delta_sec)))
    return created, updated


def seed_notes(session: Session, count: int, days_back: int) -> int:
    from app.models import Note

    notes: list[Note] = []
    for _ in range(count):
        title = gen_title()
        content = gen_content()
        tags = gen_tags()
        created_at, updated_at = rand_datetimes(days_back)
        notes.append(
            Note(
                title=title,
                content=content,
                tags=tags,
                created_at=created_at,
                updated_at=updated_at,
            )
        )
    session.add_all(notes)
    session.commit()
    return len(notes)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Seed the notes database with fake data.")
    p.add_argument("--count", type=int, default=50, help="Number of notes to insert (default: 50)")
    p.add_argument("--reset", action="store_true", help="Delete existing notes before seeding")
    p.add_argument(
        "--days-back",
        type=int,
        default=90,
        help="Limit created_at to last N days (default: 90)",
    )
    p.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Override database URL (default: env DATABASE_URL or sqlite:///./data/app.db)",
    )
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    db_url = resolve_db_url(args.db_url)
    ensure_sqlite_dir(db_url)
    engine = build_engine(db_url, allow_app_engine=(args.db_url is None))
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    ensure_schema(engine, db_url)

    deleted = 0
    with SessionLocal() as session:
        if args.reset:
            deleted = reset_notes(session)
        inserted = seed_notes(session, count=args.count, days_back=args.days_back)

    print(f"deleted={deleted} inserted={inserted} db={db_url}")


if __name__ == "__main__":
    main()
