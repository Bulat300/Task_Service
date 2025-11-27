from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.application_exceptions import DatabaseException
from src.core.transport_exceptions import NotFoundException, BadRequestException
from src.core.uow import UnitOfWork
from src.repositories.task_repository import TaskRepository
from src.repositories.outbox_repository import OutboxRepository
from src.schemas.tasks_schemas import TaskCreate
from src.models.tasks import Task, Status
from src.core.exceptions import (
    CreateTaskException,
    GetTaskException,
    DeleteTaskException,
    ListTaskException,
    GetTaskStatusException,
    UpdateTaskException,
)

class TaskService:
    def __init__(self, task_repo: TaskRepository, outbox_repo: OutboxRepository, uow: UnitOfWork):
        self.task_repo = task_repo
        self.outbox_repo = outbox_repo
        self.uow = uow

    async def create_task(self, payload: TaskCreate) -> Task:
        try:
            async with self.uow as uow:
                task = Task(
                    title=payload.title,
                    description=payload.description,
                    priority=payload.priority,
                    status=Status.PENDING,
                )

                task = await self.task_repo.create_task(uow.db, task)
                await self.outbox_repo.add_event(
                    uow.db,
                    aggregate_type="task",
                    aggregate_id=task.id,
                    event_type="task.created",
                    payload={"task_id": str(task.id), "payload": payload.model_dump()},
                )

                return task
        except DatabaseException as e:
            raise CreateTaskException(cause=e) from e

        except Exception as e:
             raise CreateTaskException(cause=e) from e

    async def list_tasks(
            self,
            page: int = 1,
            page_size: int = 20,
            priority: Optional[str] = None,
            status: Optional[str] = None
    ) -> tuple[list[Task], int]:
        try:
            async with self.uow as uow:
                skip = (page - 1) * page_size
                tasks, total = await self.task_repo.list_tasks(
                    uow.db,
                    skip=skip,
                    limit=page_size,
                    priority=priority,
                    status=status
                )

                return tasks, total
        except DatabaseException as e:
            raise ListTaskException(cause=e) from e
        except Exception as e:
            raise ListTaskException(cause=e) from e

    async def get_task(self, task_id: UUID):
        try:
            async with self.uow as uow:
                task = await self.task_repo.get_task(uow.db, task_id)

                if not task:
                    raise NotFoundException("Задача не найдена")

                return task
        except DatabaseException as e:
            raise GetTaskException(cause=e) from e
        except Exception as e:
            raise GetTaskException(cause=e) from e

    async def get_task_status(self, task_id: UUID) -> Task.status | None:
        try:
            async with self.uow as uow:
                task = await self.task_repo.get_task(uow.db, task_id)
                if not task:
                    raise NotFoundException("Задача не найдена")
                return task.status
        except DatabaseException as e:
            raise GetTaskStatusException(cause=e) from e
        except Exception as e:
            raise GetTaskStatusException(cause=e) from e

    async def delete_task(self, task_id: UUID) -> Task:
        try:
            async with self.uow as uow:
                task = await self.task_repo.get_task(uow.db, task_id)
                if not task:
                    raise NotFoundException("Задача не найдена")

                if task.status in (Status.COMPLETED, Status.FAILED):
                    raise BadRequestException("Нельзя удалить завершенную задачу")

                task.status = Status.CANCELLED
                await self.outbox_repo.add_event(
                    uow.db,
                    aggregate_type="task",
                    aggregate_id=task_id,
                    event_type="task.deleted",
                    payload={"task_id": str(task_id)},
                )

                return task
        except DatabaseException as e:
            raise DeleteTaskException(cause=e) from e
        except Exception as e:
            raise DeleteTaskException(cause=e) from e

    async def update_task_status(self, task_id: UUID, new_status: Status):
        try:
            async with self.uow as uow:
                task = await self.task_repo.get_task(uow.db, task_id)
                if not task:
                    raise NotFoundException("Задача не найдена")

                task.status = new_status
                return task

        except DatabaseException as e:
            raise UpdateTaskException(cause=e) from e
        except Exception as e:
            raise UpdateTaskException(cause=e) from e
