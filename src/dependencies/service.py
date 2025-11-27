from src.core.uow import UnitOfWork
from src.repositories.task_repository import TaskRepository
from src.repositories.outbox_repository import OutboxRepository
from src.services.task_service import TaskService
from src.core.database import async_session_maker


async def get_task_service() -> TaskService:
    repo = TaskRepository()
    outbox = OutboxRepository()
    uow = UnitOfWork(async_session_maker)

    return TaskService(
        task_repo=repo,
        outbox_repo=outbox,
        uow=uow
    )
