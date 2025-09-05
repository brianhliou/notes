from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timezone

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
    stmt = select(Note).order_by(Note.created_at.desc(), Note.id.desc())
    return list(db.execute(stmt).scalars().all())


def get_note(db: Session, note_id: int) -> Note | None:
    return db.get(Note, note_id)


def update_note(
    db: Session,
    note_id: int,
    *,
    title: str | None = None,
    content: str | None = None,
    tags: List[str] | None = None,
) -> Note | None:
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
