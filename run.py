import asyncio
import sys
import logging

from src.dependencies.service import get_task_service
from src.infra.tasks.worker import BaseWorker
from src.infra.tasks.handler import BaseMessageHandler
from src.infra.mq.client import MessageQueueClientAsync
from src.core.settings import settings
from src.services.outbox_publisher import start_outbox_publisher

logger = logging.getLogger("worker")


async def start_worker(queue_name: str):
    mq = MessageQueueClientAsync.get_instance()
    await mq.configure()
    task_service = await get_task_service()
    handler = BaseMessageHandler(logger=logger, task_service=task_service)
    worker = BaseWorker(mq_client=mq, handler=handler, logger=logger)
    await worker.run(queue_name)


async def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "worker":
        await start_worker(settings.QUEUE_MEDIUM)

    elif cmd == "worker_low":
        await start_worker(settings.QUEUE_LOW)

    elif cmd == "worker_high":
        await start_worker(settings.QUEUE_HIGH)

    elif cmd == "worker_outbox":
        await start_outbox_publisher()

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Worker stopped")
