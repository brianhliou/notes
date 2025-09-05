from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlmodel import Field, SQLModel

from app.db import get_session
from app.models import Note
from app.crud import create_note


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
