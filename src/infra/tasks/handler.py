import json
import logging
from uuid import UUID
from aio_pika import IncomingMessage

from src.models.tasks import Status
from src.services.task_service import TaskService


class BaseMessageHandler:
    def __init__(self, logger: logging.Logger, task_service: TaskService):
        self._logger = logger
        self.task_service = task_service

    async def process(self, message: IncomingMessage):
        try:
            raw = message.body.decode("utf-8")
            payload = json.loads(raw)
        except Exception:
            self._logger.error("Invalid message format")
            return
        await self.handle(payload)

    async def handle(self, payload: dict):
        try:
            self._logger.info(f"payload in handle {payload}")
            task_id = payload.get("task_id")
            if not task_id:
                self._logger.error("task_id not found in payload")
                return

            task_uuid = UUID(task_id)

            await self.task_service.update_task_status(
                task_uuid,
                Status.COMPLETED
            )

            self._logger.info(f"Task {task_id} as COMPLETED")
        except Exception as e:
            self._logger.error(f"Failed to process task completion: {e}")
