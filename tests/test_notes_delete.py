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


def test_delete_then_get_404():
    client = TestClient(app)
    r = client.post("/notes", json={"title": "t", "content": "c"})
    assert r.status_code == 201
    note_id = r.json()["id"]

    d = client.delete(f"/notes/{note_id}")
    assert d.status_code == 204

    g = client.get(f"/notes/{note_id}")
    assert g.status_code == 404
    assert g.json() == {"detail": "not found", "code": "not_found"}


def test_delete_nonexistent_is_204():
    client = TestClient(app)
    d = client.delete("/notes/99999")
    assert d.status_code == 204


def test_delete_twice_both_204():
    client = TestClient(app)
    r = client.post("/notes", json={"title": "x"})
    assert r.status_code == 201
    note_id = r.json()["id"]

    d1 = client.delete(f"/notes/{note_id}")
    assert d1.status_code == 204
    d2 = client.delete(f"/notes/{note_id}")
    assert d2.status_code == 204
