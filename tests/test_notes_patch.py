import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import get_session  # noqa: E402
from app.main import app  # noqa: E402


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


def test_patch_updates_content_only():
    client = TestClient(app)
    r = client.post("/notes", json={"title": "title", "content": "orig"})
    assert r.status_code == 201
    created = r.json()
    note_id = created["id"]

    pr = client.patch(f"/notes/{note_id}", json={"content": "updated"})
    assert pr.status_code == 200
    data = pr.json()
    assert data["id"] == note_id
    assert data["content"] == "updated"
    assert data["title"] == "title"


def test_patch_long_title_422():
    client = TestClient(app)
    r = client.post("/notes", json={"title": "ok"})
    assert r.status_code == 201
    note_id = r.json()["id"]

    long_title = "x" * 101
    pr = client.patch(f"/notes/{note_id}", json={"title": long_title})
    assert pr.status_code == 422


def test_patch_not_found_404():
    client = TestClient(app)
    pr = client.patch("/notes/99999", json={"content": "nope"})
    assert pr.status_code == 404
    assert pr.json() == {"detail": "not found", "code": "not_found"}


def test_patch_tags_updates_only_tags():
    client = TestClient(app)
    r = client.post("/notes", json={"title": "t", "content": "c", "tags": ["a"]})
    assert r.status_code == 201
    note_id = r.json()["id"]

    pr = client.patch(f"/notes/{note_id}", json={"tags": ["x", "y"]})
    assert pr.status_code == 200
    data = pr.json()
    assert data["tags"] == ["x", "y"]
    assert data["title"] == "t"
    assert data["content"] == "c"
