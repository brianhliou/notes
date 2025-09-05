import os
import sys
import time

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


def test_list_notes_sorted_by_created_desc():
    client = TestClient(app)

    # Seed three notes via POST /notes
    r1 = client.post("/notes", json={"title": "a", "content": "1"})
    assert r1.status_code == 201
    # Small sleep to ensure distinct timestamps ordering
    time.sleep(0.01)
    r2 = client.post("/notes", json={"title": "b", "content": "2"})
    assert r2.status_code == 201
    time.sleep(0.01)
    r3 = client.post("/notes", json={"title": "c", "content": "3"})
    assert r3.status_code == 201

    # GET /notes
    resp = client.get("/notes")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    items = data.get("items")
    assert isinstance(items, list)
    assert len(items) == 3

    # Expect newest-first (created_at desc): r3, r2, r1
    titles = [item["title"] for item in items]
    assert titles == ["c", "b", "a"]

