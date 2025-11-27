import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from fastapi import status
from httpx import AsyncClient


@pytest.fixture
def fake_service(monkeypatch):
    svc = AsyncMock()
    monkeypatch.setattr("app.api.v1.dependencies.get_task_service", lambda: svc)
    return svc


@pytest.mark.asyncio
async def test_create_task_ok(async_client: AsyncClient, fake_service: AsyncMock):
    tid = uuid4()
    fake_task = {
        "id": str(tid),
        "title": "test",
        "description": "x",
        "priority": "MEDIUM",
        "status": "PENDING",
        "created_at": "2024-01-01T00:00:00Z",
        "started_at": None,
        "finished_at": None,
        "result": None,
        "error": None,
    }
    fake_service.create_task.return_value = fake_task

    resp = await async_client.post("/api/v1/tasks", json={"title": "test", "description": "x", "priority": "MEDIUM"})

    assert resp.status_code == status.HTTP_201_CREATED
    assert resp.json()["id"] == str(tid)
    fake_service.create_task.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_task_not_found(async_client: AsyncClient, fake_service: AsyncMock):
    fake_service.get_task.return_value = None
    tid = uuid4()
    resp = await async_client.get(f"/api/v1/tasks/{tid}")
    assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_list_tasks(async_client: AsyncClient, fake_service: AsyncMock):
    fake_service.list_tasks.return_value = []
    resp = await async_client.get("/api/v1/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_delete_task(async_client: AsyncClient, fake_service: AsyncMock):
    fake_service.delete_task.return_value = True
    tid = uuid4()
    resp = await async_client.delete(f"/api/v1/tasks/{tid}")
    assert resp.status_code == 200
    assert resp.json() == {"deleted": True}
