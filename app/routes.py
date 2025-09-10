from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.crud import create_note, delete_note, get_note, list_notes, update_note
from app.db import get_session
from app.models import Note
from app.schemas import (
    ErrorResponse,
    ListNotesResponse,
    NoteCreate,
    NoteRead,
    NoteUpdate,
    OpenAPIExamples,
)

router = APIRouter()


@router.get("/ping", tags=["Meta"])
def ping() -> dict:
    """Simple ping endpoint.

    Summary: Lightweight liveness probe for CI/tools.
    """
    return {"ok": True}


@router.post(
    "/notes",
    response_model=NoteRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Notes"],
    responses={
        201: {
            "description": "Note created",
            "content": {"application/json": {"examples": OpenAPIExamples.create_response}},
        },
        422: {"model": ErrorResponse, "content": {"application/json": {"examples": OpenAPIExamples.errors}}},
    },
)
def create_note_endpoint(
    payload: NoteCreate = Body(...),
    db: Session = Depends(get_session),
) -> Note:
    """Create a new note.

    Summary: Creates a note with optional content and tags.
    """
    return create_note(db, title=payload.title, content=payload.content or "", tags=payload.tags)


@router.get(
    "/notes",
    response_model=ListNotesResponse,
    status_code=status.HTTP_200_OK,
    tags=["Notes"],
    responses={
        200: {
            "description": "List notes (newest first).",
            "content": {"application/json": {"examples": OpenAPIExamples.list_response}},
        }
    },
)
def list_notes_endpoint(db: Session = Depends(get_session)) -> dict:
    """List all notes ordered by newest first.

    Summary: Returns notes sorted by created_at desc.
    """
    items = list_notes(db)
    return {"items": items}


@router.get(
    "/notes/{note_id}",
    response_model=NoteRead,
    tags=["Notes"],
    responses={
        404: {
            "model": ErrorResponse,
            "content": {"application/json": {"examples": {"not_found": OpenAPIExamples.errors["not_found"]}}},
        }
    },
)
def get_note_endpoint(note_id: int, db: Session = Depends(get_session)) -> Note:
    """Get a single note by id.

    Summary: Fetch one note.
    """
    note = get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="not found")
    return note


@router.patch(
    "/notes/{note_id}",
    response_model=NoteRead,
    tags=["Notes"],
    responses={
        400: {"model": ErrorResponse},
        404: {
            "model": ErrorResponse,
            "content": {"application/json": {"examples": {"not_found": OpenAPIExamples.errors["not_found"]}}},
        },
        422: {"model": ErrorResponse, "content": {"application/json": {"examples": {"validation": OpenAPIExamples.errors["validation"]}}}},
    },
)
def patch_note_endpoint(
    note_id: int,
    payload: NoteUpdate = Body(...),
    db: Session = Depends(get_session),
) -> Note:
    """Partially update a note.

    Summary: Update any subset of fields.
    """
    note = update_note(db, note_id, title=payload.title, content=payload.content, tags=payload.tags)
    if not note:
        raise HTTPException(status_code=404, detail="not found")
    return note


@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Notes"],
    responses={204: {"description": "Idempotent delete"}},
)
def delete_note_endpoint(note_id: int, db: Session = Depends(get_session)) -> Response:
    """Delete a note by id.

    Summary: Idempotent delete; returns 204 even if missing.
    """
    # Idempotent delete: return 204 even if not found
    delete_note(db, note_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
