# src/app/mq/client.py
import asyncio
import json
import math
from typing import Any, Callable, Optional, Coroutine

import aio_pika
import aiormq
from aio_pika import ExchangeType, Message, DeliveryMode
from aio_pika.abc import AbstractChannel, AbstractIncomingMessage

from src.core.logging import get_logger
from src.core.settings import settings

logger = get_logger("MessageQueueClientAsync")


class MessageQueueClientAsync:
    _instance: Optional["MessageQueueClientAsync"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MessageQueueClientAsync, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "MessageQueueClientAsync":
        if cls._instance is None:
            cls._instance = MessageQueueClientAsync()
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._pub_channel: Optional[AbstractChannel] = None
        self._consumer_channel: Optional[AbstractChannel] = None
        self._exchange: Optional[aio_pika.Exchange] = None
        self._lock = asyncio.Lock()
        self._closing = False

    async def configure(self) -> None:
        async with self._lock:
            if self._connection and not self._connection.is_closed:
                return

            logger.info("Connecting to RabbitMQ: %s", settings.RABBITMQ_URL)
            try:
                self._connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
                self._pub_channel = await self._connection.channel()
                self._consumer_channel = await self._connection.channel()
                self._exchange = await self._pub_channel.declare_exchange(settings.EXCHANGE_TASKS, ExchangeType.DIRECT, durable=True)

                dlx = await self._pub_channel.declare_exchange(settings.DLX, ExchangeType.FANOUT, durable=True)
                dlq_queue = await self._pub_channel.declare_queue(settings.DLQ, durable=True)
                await dlq_queue.bind(dlx)

                await self._declare_queue_with_dlx(settings.QUEUE_HIGH, settings.ROUTING_KEY_HIGH)
                await self._declare_queue_with_dlx(settings.QUEUE_MEDIUM, settings.ROUTING_KEY_MEDIUM)
                await self._declare_queue_with_dlx(settings.QUEUE_LOW, settings.ROUTING_KEY_LOW)

                logger.info("RabbitMQ configured, exchange and queues declared.")
            except Exception as exc:
                logger.exception("Failed to configure RabbitMQ client: %s", exc)
                raise

    async def _declare_queue_with_dlx(self, queue_name: str, routing_key: str):
        args = {
            "x-dead-letter-exchange": settings.DLX,
        }
        try:
            queue = await self._pub_channel.declare_queue(queue_name)
            logger.info("Queue '%s' already exists, skipping declare", queue_name)
        except aiormq.exceptions.ChannelPreconditionFailed:
            logger.warning(
                "Queue '%s' exists with different arguments. Deleting and recreating...", queue_name
            )
            await self._pub_channel.queue_delete(queue_name)
            queue = await self._pub_channel.declare_queue(queue_name, durable=True, arguments=args)

        except aio_pika.exceptions.ChannelClosed:
            queue = await self._pub_channel.declare_queue(queue_name, durable=True, arguments=args)

        await queue.bind(self._exchange, routing_key=routing_key)
        logger.info("Queue '%s' bound to exchange '%s' with routing_key '%s'", queue_name, self._exchange.name,
                    routing_key)

    async def close(self):
        self._closing = True
        try:
            if self._connection:
                await self._connection.close()
        except Exception:
            logger.exception("Error closing RabbitMQ connection")

    async def _publish(self, body: bytes, routing_key: str = "", exchange: Optional[str] = None, max_retries: int = 5):
        attempt = 0
        base_delay = 1.0
        while True:
            try:
                if self._pub_channel is None or self._pub_channel.is_closed:
                    await self.configure()
                message = aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
                await self._exchange.publish(message, routing_key=routing_key)
                return
            except (aio_pika.exceptions.AMQPConnectionError, aiormq.exceptions.ChannelClosed) as ex:
                attempt += 1
                if attempt > max_retries:
                    logger.exception("Max publish retries reached; message lost")
                    raise
                delay = base_delay * (2 ** (attempt - 1))
                jitter = min(0.5, delay * 0.1)
                await asyncio.sleep(delay + (jitter * (math.random() - 0.5) if hasattr(math, "random") else 0))
                logger.warning("Publish failed (attempt %d/%d), reconnecting: %s", attempt, max_retries, ex)
                try:
                    await self.configure()
                except Exception:
                    logger.warning("Reconfigure failed; will retry publish after delay")
            except Exception as ex:
                logger.exception("Unexpected publish error: %s", ex)
                raise

    async def publish_json(self, payload: dict, priority: str = "medium"):
        rk = priority.lower()
        if rk not in (settings.ROUTING_KEY_HIGH, settings.ROUTING_KEY_MEDIUM, settings.ROUTING_KEY_LOW):
            rk = settings.ROUTING_KEY_MEDIUM
        body = json.dumps(payload).encode()
        await self._publish(body=body, routing_key=rk)

    async def basic_consume(self, queue_name: str, callback: Callable[[AbstractIncomingMessage], Coroutine[Any, Any, None]], prefetch_count: int = settings.DEFAULT_PREFETCH_COUNT):
        if self._consumer_channel is None or self._consumer_channel.is_closed:
            await self.configure()
        await self._consumer_channel.set_qos(prefetch_count=prefetch_count)
        queue = await self._consumer_channel.get_queue(queue_name)
        await queue.consume(callback, no_ack=False)
        logger.info("Consuming on queue %s with prefetch=%d", queue_name, prefetch_count)

    async def handle_failed_message(self, message: AbstractIncomingMessage):

        headers = dict(message.headers or {})
        attempts = int(headers.get("attempts", 0))

        next_attempt = attempts + 1
        if next_attempt <= settings.MAX_ATTEMPTS:
            await self.republish_to_retry(message, attempt=next_attempt)
            await message.ack()
        else:
            await self.send_to_dlq(message, reason=f"exhausted_attempts={attempts}")
            await message.ack()

    async def send_to_dlq(self, message: AbstractIncomingMessage, reason: str = ""):
        headers = dict(message.headers or {})
        headers["x-death-reason"] = reason
        msg = Message(body=message.body, delivery_mode=DeliveryMode.PERSISTENT, headers=headers)

        if self._exchange is None:
            await self.configure()

        dlx_exchange = await self._pub_channel.get_exchange(settings.DLX)
        if dlx_exchange is None:
            dlx_exchange = await self._pub_channel.declare_exchange(settings.DLX, ExchangeType.FANOUT, durable=True)

        await dlx_exchange.publish(msg, routing_key="")
        logger.warning("Moved message to DLQ: %s", headers.get("message_id", "<no-id>"))

    async def republish_to_retry(self, message: AbstractIncomingMessage, attempt: int):
        idx = min(attempt - 1, len(settings.RETRY_DELAYS_MS) - 1)
        delay_ms = settings.RETRY_DELAYS_MS[idx]
        retry_queue = f"retry_{delay_ms}"

        headers = dict(message.headers or {})
        headers["attempts"] = attempt

        msg = Message(body=message.body, delivery_mode=DeliveryMode.PERSISTENT, headers=headers)
        await self._pub_channel.default_exchange.publish(msg, routing_key=retry_queue)
        logger.info("Republished message to retry queue %s (attempt=%d)", retry_queue, attempt)
