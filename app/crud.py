from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Note


def create_note(
    db: Session, *, title: str, content: str = "", tags: Optional[List[str]] = None
) -> Note:
    note = Note(title=title, content=content or "", tags=tags or [])
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
