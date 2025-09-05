
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from sqlmodel import Field, SQLModel

from app.crud import create_note, delete_note, get_note, list_notes, update_note
from app.db import get_session
from app.models import Note

router = APIRouter()


@router.get("/ping")
def ping() -> dict:
    return {"ok": True}


class NoteCreate(SQLModel):
    title: str = Field(max_length=100)
    content: str | None = ""
    tags: list[str] | None = None


@router.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
def create_note_endpoint(payload: NoteCreate, db: Session = Depends(get_session)) -> Note:
    return create_note(db, title=payload.title, content=payload.content or "", tags=payload.tags)


@router.get("/notes")
def list_notes_endpoint(db: Session = Depends(get_session)) -> dict:
    items = list_notes(db)
    return {"items": items}


@router.get("/notes/{note_id}", response_model=Note)
def get_note_endpoint(note_id: int, db: Session = Depends(get_session)) -> Note:
    note = get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="not found")
    return note


class NoteUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=100)
    content: str | None = None
    tags: list[str] | None = None


@router.patch("/notes/{note_id}", response_model=Note)
def patch_note_endpoint(
    note_id: int, payload: NoteUpdate, db: Session = Depends(get_session)
) -> Note:
    note = update_note(db, note_id, title=payload.title, content=payload.content, tags=payload.tags)
    if not note:
        raise HTTPException(status_code=404, detail="not found")
    return note


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note_endpoint(note_id: int, db: Session = Depends(get_session)) -> Response:
    # Idempotent delete: return 204 even if not found
    delete_note(db, note_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
