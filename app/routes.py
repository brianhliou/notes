import json
from datetime import datetime
from typing import Iterable

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.crud import (
    bulk_insert_notes,
    create_note,
    delete_note,
    get_note,
    iter_all_notes,
    list_notes,
    update_note,
)
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
    "/notes/export",
    tags=["Notes"],
    responses={
        200: {
            "content": {
                "application/x-ndjson": {},
                "application/jsonl": {},
            },
            "description": "Stream notes as JSON Lines (newest first).",
        }
    },
)
def export_notes_endpoint(db: Session = Depends(get_session)) -> StreamingResponse:
    """Export all notes as JSON Lines.

    Summary: Streams one JSON object per line.
    """

    def line_iter() -> Iterable[bytes]:
        for n in iter_all_notes(db):
            obj = {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "tags": n.tags,
                "created_at": n.created_at.isoformat() if isinstance(n.created_at, datetime) else str(n.created_at),
                "updated_at": n.updated_at.isoformat() if isinstance(n.updated_at, datetime) else (str(n.updated_at) if n.updated_at is not None else None),
            }
            yield (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")

    headers = {
        "Content-Disposition": 'attachment; filename="notes.jsonl"',
    }
    return StreamingResponse(line_iter(), media_type="application/x-ndjson", headers=headers)


@router.post(
    "/notes/import",
    tags=["Notes"],
    responses={
        200: {"description": "Inserted notes count."},
        400: {"description": "Invalid payload."},
    },
)
async def import_notes_endpoint(request: Request, db: Session = Depends(get_session)) -> dict:
    """Bulk import notes from JSON Lines.

    Summary: All-or-nothing import with basic validation.
    """
    MAX_BYTES = 10 * 1024 * 1024
    MAX_LINES = 10_000

    body = await request.body()
    if len(body) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="payload too large (max 10MB)")

    raw_lines = body.split(b"\n")
    items: list[dict] = []
    for idx, raw in enumerate(raw_lines, start=1):
        if idx > MAX_LINES:
            raise HTTPException(status_code=400, detail="too many lines (max 10000)")
        if not raw:
            continue
        line = raw.strip()
        if not line or line.startswith(b"#"):
            continue
        try:
            data = json.loads(line)
        except Exception:
            raise HTTPException(status_code=400, detail=f"invalid JSON on line {idx}")

        # Normalize and validate
        title = data.get("title")
        if not isinstance(title, str) or not (1 <= len(title) <= 100):
            raise HTTPException(status_code=400, detail=f"invalid title on line {idx}")

        content = data.get("content", "")
        if not isinstance(content, str):
            raise HTTPException(status_code=400, detail=f"invalid content on line {idx}")

        tags = data.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            raise HTTPException(status_code=400, detail=f"invalid tags on line {idx}")

        def _parse_dt(value: object, field: str) -> datetime | None:
            if value is None:
                return None
            if not isinstance(value, str):
                raise HTTPException(status_code=400, detail=f"invalid {field} on line {idx}")
            v = value
            if v.endswith("Z"):
                v = v[:-1] + "+00:00"
            try:
                return datetime.fromisoformat(v)
            except Exception:
                raise HTTPException(status_code=400, detail=f"invalid {field} on line {idx}")

        created_at = _parse_dt(data.get("created_at"), "created_at") or datetime.utcnow()
        updated_at = _parse_dt(data.get("updated_at"), "updated_at") or created_at

        items.append(
            {
                "title": title,
                "content": content,
                "tags": tags,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    # Transactional bulk insert
    try:
        inserted = bulk_insert_notes(db, items)
    except HTTPException:
        raise
    except Exception:
        # Rollback is handled inside CRUD if needed; ensure no partials on failure
        db.rollback()
        raise HTTPException(status_code=400, detail="import failed")

    return {"inserted": inserted}


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
