from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session
from sqlmodel import select

from app.models import Note


def create_note(
    db: Session, *, title: str, content: str = "", tags: Optional[List[str]] = None
) -> Note:
    note = Note(title=title, content=content or "", tags=tags or [])
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def list_notes(db: Session) -> list[Note]:
    # Order by created_at desc, then id desc for deterministic ties
    stmt = select(Note).order_by(
        desc(Note.created_at),  # type: ignore[arg-type]
        desc(Note.id),  # type: ignore[arg-type]
    )
    return list(db.execute(stmt).scalars().all())


def get_note(db: Session, note_id: int) -> Optional[Note]:
    return db.get(Note, note_id)


def update_note(
    db: Session,
    note_id: int,
    *,
    title: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Optional[Note]:
    note = db.get(Note, note_id)
    if not note:
        return None
    if title is not None:
        note.title = title
    if content is not None:
        note.content = content
    if tags is not None:
        note.tags = tags
    note.updated_at = datetime.now(timezone.utc)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note_id: int) -> bool:
    note = db.get(Note, note_id)
    if not note:
        return False
    db.delete(note)
    db.commit()
    return True


from collections.abc import Iterable


def iter_all_notes(db: Session) -> Iterable[Note]:
    """Yield all notes ordered newest-first (created_at desc, id desc)."""
    stmt = select(Note).order_by(
        desc(Note.created_at),  # type: ignore[arg-type]
        desc(Note.id),  # type: ignore[arg-type]
    )
    for note in db.execute(stmt).scalars():
        yield note


def bulk_insert_notes(db: Session, items: list[dict]) -> int:
    """Insert many notes in one transaction. Returns inserted count."""
    notes: list[Note] = []
    for data in items:
        notes.append(
            Note(
                title=data["title"],
                content=data.get("content", ""),
                tags=data.get("tags", []),
                created_at=data.get("created_at", datetime.now(timezone.utc)),
                updated_at=data.get("updated_at", data.get("created_at", datetime.now(timezone.utc))),
            )
        )
    if notes:
        db.add_all(notes)
        db.commit()
    return len(notes)
