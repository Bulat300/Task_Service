from pydantic import BaseModel, constr, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from src.models.tasks import Priority, Status

class TaskCreate(BaseModel):
    title: constr(strip_whitespace=True, min_length=1, max_length=255)
    description: Optional[str]
    priority: Priority = Priority.MEDIUM

class TaskRead(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    priority: Priority
    status: Status
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    result: Optional[str]
    error: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class TaskList(BaseModel):
    items: list[TaskRead]
    total: int
    page: int
    page_size: int


class DeleteTaskResponse(BaseModel):
    deleted: bool

    model_config = ConfigDict(from_attributes=True)
