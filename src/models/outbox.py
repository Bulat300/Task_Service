from sqlalchemy import Column, String, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from src.models.base import Base
import uuid

class Outbox(Base):
    __tablename__ = 'outbox'
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type = Column(String(50), nullable=False)
    aggregate_id = Column(PG_UUID(as_uuid=True), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent = Column(Boolean, default=False, nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
