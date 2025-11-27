import uvicorn
from fastapi import FastAPI
from src.api.v1.endpoints.tasks import router as v1_router
from src.core.logging import get_logger
from fastapi.middleware.cors import CORSMiddleware

from src.core.register_error import register_error_handlers

get_logger("Main")

app = FastAPI(title="Async Task Service", version="1.0")
register_error_handlers(app)
app.include_router(v1_router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
    )