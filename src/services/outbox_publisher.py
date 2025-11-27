import asyncio
import json
from datetime import datetime
from typing import Optional

from sqlalchemy import select
import aio_pika
from src.core.settings import settings
from src.models.outbox import Outbox
from src.core.database import async_session_maker

from src.core.logging import get_logger

logger = get_logger("Outbox_publisher")

class OutboxPublisher:
    def __init__(self):
        self.conn: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.abc.AbstractChannel] = None

    async def start(self):
        self.conn = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        self.channel = await self.conn.channel()

    async def publish_outbox_once(self, limit: int = 10):
        async with async_session_maker() as db:
            async with db.begin():
                q = await db.execute(
                    select(Outbox)
                    .where(Outbox.sent == False)
                    .limit(limit)
                    .with_for_update(skip_locked=True)
                )
                rows = q.scalars().all()
                for row in rows:
                    priority = row.payload.get('payload', {}).get('priority', 'medium').lower()
                    logger.info(f"row.payload {row.payload}")
                    msg = aio_pika.Message(
                        body=json.dumps(row.payload).encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                    )
                    await self.channel.default_exchange.publish(msg, routing_key=priority)
                    row.sent = True
                    row.sent_at = datetime.now()
                await db.commit()


async def start_outbox_publisher(poll_interval: float = 1.0):
    poll_interval = float(poll_interval)
    publisher = OutboxPublisher()
    await publisher.start()
    while True:
        try:
            await publisher.publish_outbox_once()
        except Exception as e:
            logger.exception("Outbox publisher error: %s", e)
        await asyncio.sleep(poll_interval)
