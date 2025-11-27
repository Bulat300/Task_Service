import asyncio
import logging
from aio_pika import IncomingMessage
from src.infra.tasks.handler import BaseMessageHandler
from src.infra.mq.client import MessageQueueClientAsync


class BaseWorker:
    def __init__(self, mq_client: MessageQueueClientAsync, handler: BaseMessageHandler, logger: logging.Logger):
        self._mq = mq_client
        self._handler = handler
        self._logger = logger

    async def run(self, queue_name: str):
        async def _safe_consume(message: IncomingMessage):
            try:
                self._logger.info("Worker process message: %s", message)
                await self._handler.process(message)
                await message.ack()
            except Exception as ex:
                self._logger.exception("Worker failed to process message: %s", ex)
                try:
                    await self._mq.handle_failed_message(message)
                except Exception as inner:
                    self._logger.exception("Failed handling failed message: %s", inner)
                    await message.nack(requeue=False)

        try:
            self._logger.info("queue_name: %s", queue_name)
            await self._mq.basic_consume(queue_name, _safe_consume)
            await asyncio.Future()
        except Exception as ex:
            self._logger.error(f"Worker crashed: {ex}")
            await asyncio.sleep(5)
            return await self.run(queue_name)
