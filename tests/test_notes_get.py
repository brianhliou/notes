import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app  # noqa: E402
from app.db import get_session  # noqa: E402


@pytest.fixture(autouse=True)
def override_db_dependency():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    # Import models to ensure tables are registered
    from app import models as _models  # noqa: F401

    SQLModel.metadata.create_all(engine)

    def _get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    yield
    app.dependency_overrides.clear()


def test_get_note_success_and_not_found():
    client = TestClient(app)

    # Seed a note
    r = client.post("/notes", json={"title": "hello", "content": "world"})
    assert r.status_code == 201
    created = r.json()
    note_id = created["id"]

    # GET existing note
    resp = client.get(f"/notes/{note_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == note_id
    assert data["title"] == "hello"
    assert data["content"] == "world"
    assert data["tags"] == []

    # GET non-existing note -> 404
    resp2 = client.get("/notes/99999")
    assert resp2.status_code == 404
    assert resp2.json() == {"detail": "not found"}

