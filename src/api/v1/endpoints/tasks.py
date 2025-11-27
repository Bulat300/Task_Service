from typing import Optional
from fastapi import APIRouter, Depends
from src.schemas.tasks_schemas import TaskCreate, TaskRead, TaskList, DeleteTaskResponse
from uuid import UUID
from src.services.task_service import TaskService
from src.dependencies.service import get_task_service

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

@router.post("", response_model=TaskRead, status_code=201)
async def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
):
    task = await service.create_task(payload)
    return task

@router.get("", response_model=TaskList)
async def list_tasks(
    page: int = 1,
    page_size: int = 20,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    service: TaskService = Depends(get_task_service)
):
    tasks, total = await service.list_tasks(page=page, page_size=page_size, priority=priority, status=status)

    return TaskList(
        items=[TaskRead.model_validate(task) for task in tasks],
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
        task_id: UUID,
        service: TaskService = Depends(get_task_service)
):
    return await service.get_task(task_id)

@router.delete("/{task_id}", response_model=DeleteTaskResponse)
async def delete_task(
        task_id: UUID,
        service: TaskService = Depends(get_task_service)
):
    await service.delete_task(task_id)
    return DeleteTaskResponse(deleted=True)

@router.get("/{task_id}")
async def get_task_status(task_id: UUID, service: TaskService = Depends(get_task_service)):
    status = await service.get_task_status(task_id)
    return {"task_id": str(task_id), "status": status}


