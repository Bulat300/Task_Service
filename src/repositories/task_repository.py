from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.tasks import Task
from uuid import UUID
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from src.core.application_exceptions import DatabaseException


class TaskRepository:
    async def create_task(self, db: AsyncSession, task: Task) -> Task:
        try:
            db.add(task)
            await db.flush()
            return task
        except SQLAlchemyError as e:
            raise DatabaseException("Ошибка сохранения задачи", cause=e)

    async def get_task(self, db: AsyncSession, task_id: UUID) -> Optional[Task]:
        try:
            q = await db.execute(select(Task).where(Task.id == task_id))
            return q.scalars().first()
        except SQLAlchemyError as e:
            raise DatabaseException("Ошибка чтения задачи", cause=e)

    async def list_tasks(
            self,
            db: AsyncSession,
            *,
            skip: int = 0,
            limit: int = 20,
            priority: Optional[str] = None,
            status: Optional[str] = None
    ) -> tuple[list[Task], int]:
        try:
            stmt = select(Task)
            if priority:
                stmt = stmt.where(Task.priority == priority)
            if status:
                stmt = stmt.where(Task.status == status)
            stmt = stmt.order_by(Task.created_at.desc()).offset(skip).limit(limit)
            q = await db.execute(stmt)
            tasks = q.scalars().all()

            count_stmt = select(func.count(Task.id))
            if priority:
                count_stmt = count_stmt.where(Task.priority == priority)
            if status:
                count_stmt = count_stmt.where(Task.status == status)
            total_q = await db.execute(count_stmt)
            total = total_q.scalar_one()

            return tasks, total
        except SQLAlchemyError as e:
            raise DatabaseException("Ошибка получения списка задач", cause=e)