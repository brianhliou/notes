import asyncio
import pytest


pytestmark = pytest.mark.anyio


async def test_post_note_defaults(async_client):
    resp = await async_client.post("/notes", json={"title": "t"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "t"
    assert data["content"] == ""
    assert data["tags"] == []


async def test_post_title_too_long(async_client):
    long_title = "x" * 101
    resp = await async_client.post("/notes", json={"title": long_title})
    assert resp.status_code == 422
    body = resp.json()
    assert body.get("code") == "validation_error"


async def test_list_notes_sorted(async_client):
    await async_client.post("/notes", json={"title": "a"})
    await asyncio.sleep(0.01)
    await async_client.post("/notes", json={"title": "b"})
    await asyncio.sleep(0.01)
    await async_client.post("/notes", json={"title": "c"})

    resp = await async_client.get("/notes")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert [i["title"] for i in items] == ["c", "b", "a"]


async def test_get_note_and_404(async_client):
    created = (await async_client.post("/notes", json={"title": "hello", "content": "world"})).json()
    note_id = created["id"]

    g = await async_client.get(f"/notes/{note_id}")
    assert g.status_code == 200
    data = g.json()
    assert data["id"] == note_id
    assert data["title"] == "hello"
    assert data["content"] == "world"

    g2 = await async_client.get("/notes/99999")
    assert g2.status_code == 404
    assert g2.json() == {"detail": "not found", "code": "not_found"}


async def test_patch_partial_updates_and_validation(async_client):
    created = (await async_client.post("/notes", json={"title": "t", "content": "c", "tags": ["a"]})).json()
    note_id = created["id"]
    prev_updated_at = created["updated_at"]

    pr = await async_client.patch(f"/notes/{note_id}", json={"content": "updated"})
    assert pr.status_code == 200
    pdata = pr.json()
    assert pdata["content"] == "updated"
    assert pdata["title"] == "t"
    assert pdata["tags"] == ["a"]
    assert pdata["updated_at"] != prev_updated_at

    # title too long
    long_title = "x" * 101
    pr2 = await async_client.patch(f"/notes/{note_id}", json={"title": long_title})
    assert pr2.status_code == 422
    assert pr2.json().get("code") == "validation_error"

    # tags wrong type
    pr3 = await async_client.patch(f"/notes/{note_id}", json={"tags": "not-a-list"})
    assert pr3.status_code == 422
    assert pr3.json().get("code") == "validation_error"

    # missing id
    pr4 = await async_client.patch("/notes/99999", json={"content": "x"})
    assert pr4.status_code == 404
    assert pr4.json() == {"detail": "not found", "code": "not_found"}


async def test_delete_idempotent_and_get_404(async_client):
    created = (await async_client.post("/notes", json={"title": "x"})).json()
    note_id = created["id"]

    d1 = await async_client.delete(f"/notes/{note_id}")
    assert d1.status_code == 204
    d2 = await async_client.delete(f"/notes/{note_id}")
    assert d2.status_code == 204

    g = await async_client.get(f"/notes/{note_id}")
    assert g.status_code == 404
    assert g.json() == {"detail": "not found", "code": "not_found"}


async def test_health_and_ready(async_client):
    h = await async_client.get("/health")
    assert h.status_code == 200
    assert h.json() == {"status": "ok"}

    r = await async_client.get("/ready")
    assert r.status_code == 200
