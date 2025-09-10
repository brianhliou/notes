from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Human-readable error message.")
    code: Literal[
        "not_found",
        "validation_error",
        "bad_request",
        "conflict",
        "internal_error",
    ] = Field(
        default="bad_request",
        description="Stable machine-readable error code.",
        examples=["validation_error"],
    )


class NoteBase(BaseModel):
    title: str = Field(
        ..., description="Short title for the note (1–100 chars).", examples=["Grocery List"], min_length=1, max_length=100
    )
    content: str = Field(
        default="",
        description="Free-form note content (Markdown allowed).",
        examples=["- apples\n- bananas"],
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Optional tags for organization.",
        examples=[["personal", "shopping"]],
    )


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    """
    Partial update payload. All fields are optional.
    At least one field should be provided by clients at runtime.
    """

    title: str | None = Field(
        default=None, description="New title (1–100 chars).", examples=["Updated title"], min_length=1, max_length=100
    )
    content: str | None = Field(
        default=None, description="New content.", examples=["Updated body"]
    )
    tags: list[str] | None = Field(
        default=None, description="Replace tags.", examples=[["work", "todo"]]
    )


class NoteRead(BaseModel):
    id: int = Field(..., examples=[123])
    title: str = Field(..., examples=["Grocery List"])
    content: str = Field(..., examples=["- apples\n- bananas"])
    tags: list[str] = Field(default_factory=list, examples=[["personal", "shopping"]])
    created_at: datetime = Field(..., examples=["2024-01-01T12:00:00Z"])
    updated_at: datetime | None = Field(default=None, examples=["2024-01-01T12:34:56Z"])


class ListNotesResponse(BaseModel):
    items: list[NoteRead] = Field(
        default_factory=list, description="Newest-first list of notes."
    )


class OpenAPIExamples:
    create_request = {
        "valid": {
            "summary": "Create a note",
            "value": {"title": "Trip", "content": "Pack bags", "tags": ["travel"]},
        }
    }

    create_response = {
        "created": {
            "summary": "Created note",
            "value": {
                "id": 1,
                "title": "Trip",
                "content": "Pack bags",
                "tags": ["travel"],
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            },
        }
    }

    list_response = {
        "two_items": {
            "summary": "Two notes, newest first",
            "value": {
                "items": [
                    {
                        "id": 2,
                        "title": "B",
                        "content": "2",
                        "tags": [],
                        "created_at": "2024-01-02T00:00:00Z",
                        "updated_at": "2024-01-02T00:00:00Z",
                    },
                    {
                        "id": 1,
                        "title": "A",
                        "content": "1",
                        "tags": [],
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    },
                ]
            },
        }
    }

    get_response = {
        "found": {
            "summary": "Existing note",
            "value": {
                "id": 1,
                "title": "Hello",
                "content": "World",
                "tags": ["greeting"],
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:34:56Z",
            },
        }
    }

    patch_request = {
        "update_content": {
            "summary": "Update content",
            "value": {"content": "Updated"},
        },
        "update_tags": {"summary": "Replace tags", "value": {"tags": ["x", "y"]}},
    }

    delete_response = {
        "no_content": {
            "summary": "Deleted",
            "value": None,
        }
    }

    errors = {
        "not_found": {"summary": "Not found", "value": {"detail": "not found", "code": "not_found"}},
        "validation": {
            "summary": "Validation error",
            "value": {"detail": "validation failed", "code": "validation_error"},
        },
    }
