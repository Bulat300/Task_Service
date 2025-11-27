import asyncio
import pytest
from datetime import datetime

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import async_session_maker

from src.models.tasks import Task, Status
from src.services.outbox_publisher import OutboxPublisher
from src.infra.mq.client import MessageQueueClientAsync
from src.infra.tasks.worker import BaseWorker
from src.infra.tasks.handler import BaseMessageHandler
from src.services.task_service import TaskService


class TestHandler(BaseMessageHandler):
    def __init__(self, logger=None, task_service=TaskService):
        super().__init__(logger=logger, task_service=task_service)

    async def handle(self, payload: dict):
        task_id = payload.get("task_id") or payload.get("payload", {}).get("task_id")
        if not task_id:
            return

        async with async_session_maker() as db:
            q = await db.execute(select(Task).where(Task.id == task_id))
            task = q.scalars().first()
            if task:
                task.status = Status.COMPLETED
                task.finished_at = datetime.utcnow()
                db.add(task)
                await db.commit()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_task_lifecycle(
    async_client: AsyncClient,
    test_db: AsyncSession,
    mq_client: MessageQueueClientAsync,
    task_service: TaskService
):
    resp = await async_client.post("/api/v1/tasks", json={"title": "int test", "description": "x", "priority": "HIGH"})
    assert resp.status_code == 201
    task_obj = resp.json()
    task_id = task_obj["id"]

    publisher = OutboxPublisher()
    await publisher.start()
    await publisher.publish_outbox_once(limit=10)

    handler = BaseMessageHandler(logger=None, task_service=task_service)
    worker = BaseWorker(mq_client, handler, logger=None)

    worker_task = asyncio.create_task(worker.run("tasks_high"))
    await asyncio.sleep(1.5)

    q = await test_db.execute(select(Task).where(Task.id == task_id))
    task = q.scalars().first()
    assert task is not None
    assert task.status == Status.COMPLETED

    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
