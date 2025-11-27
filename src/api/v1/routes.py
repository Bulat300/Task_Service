from fastapi import APIRouter

from src.api.v1.endpoints.tasks import router as tasks_router

routers = APIRouter()
router_list = [
    tasks_router
]

for router in router_list:
    routers.include_router(router)