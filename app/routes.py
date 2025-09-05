from typing import List, Optional

from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlmodel import Field, SQLModel

from app.db import get_session
from app.models import Note
from app.crud import create_note, list_notes, get_note, update_note, delete_note


router = APIRouter()


@router.get("/ping")
def ping() -> dict:
    return {"ok": True}


class NoteCreate(SQLModel):
    title: str = Field(max_length=100)
    content: Optional[str] = ""
    tags: Optional[List[str]] = None


@router.post("/notes", response_model=Note, status_code=status.HTTP_201_CREATED)
def create_note_endpoint(payload: NoteCreate, db=Depends(get_session)) -> Note:
    return create_note(db, title=payload.title, content=payload.content or "", tags=payload.tags)


@router.get("/notes")
def list_notes_endpoint(db=Depends(get_session)) -> dict:
    items = list_notes(db)
    return {"items": items}


@router.get("/notes/{note_id}", response_model=Note)
def get_note_endpoint(note_id: int, db=Depends(get_session)) -> Note:
    note = get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="not found")
    return note


class NoteUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=100)
    content: Optional[str] = None
    tags: Optional[List[str]] = None


@router.patch("/notes/{note_id}", response_model=Note)
def patch_note_endpoint(note_id: int, payload: NoteUpdate, db=Depends(get_session)) -> Note:
    note = update_note(db, note_id, title=payload.title, content=payload.content, tags=payload.tags)
    if not note:
        raise HTTPException(status_code=404, detail="not found")
    return note


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note_endpoint(note_id: int, db=Depends(get_session)) -> Response:
    # Idempotent delete: return 204 even if not found
    delete_note(db, note_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
