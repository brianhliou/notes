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


def test_create_note_minimal():
    client = TestClient(app)
    resp = client.post("/notes", json={"title": "t", "content": "c"})
    assert resp.status_code == 201
    data = resp.json()
    assert isinstance(data.get("id"), int)
    assert data["title"] == "t"
    assert data["content"] == "c"
    assert data["tags"] == []


def test_create_note_title_too_long():
    client = TestClient(app)
    long_title = "x" * 101
    resp = client.post("/notes", json={"title": long_title})
    assert resp.status_code == 422
