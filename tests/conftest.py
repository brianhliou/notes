import os
import sys
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine
from httpx import AsyncClient, ASGITransport

# Ensure project root on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app as fastapi_app  # noqa: E402
from app.db import get_session  # noqa: E402


@pytest.fixture
def app():
    return fastapi_app


@pytest.fixture
def db_override(app):
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    # Import models so tables are registered
    from app import models as _models  # noqa: F401

    SQLModel.metadata.create_all(engine)

    def _get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    try:
        yield
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
async def async_client(app, db_override):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def anyio_backend():
    # Use asyncio to avoid requiring trio in the test environment
    return "asyncio"
