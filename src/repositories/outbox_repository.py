from sqlalchemy.ext.asyncio import AsyncSession
from src.models.outbox import Outbox

class OutboxRepository:
    async def add_event(self, db: AsyncSession, aggregate_type: str, aggregate_id, event_type: str, payload: dict):
        ev = Outbox(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            payload=payload,
        )
        db.add(ev)
        return ev
