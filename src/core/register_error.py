from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from src.core.application_exceptions import ApplicationException
from sqlalchemy.exc import IntegrityError
from src.core.transport_exceptions import CustomHTTPException
from fastapi.exceptions import RequestValidationError


def register_error_handlers(app: FastAPI):
    @app.exception_handler(CustomHTTPException)
    async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.message}
        )

    @app.exception_handler(ApplicationException)
    async def app_handler(request: Request, exc: ApplicationException):
        data = {"message": exc.message}

        if hasattr(exc, "cause") and exc.cause:
            data["error"] = exc.cause.__class__.__name__

        return JSONResponse(status_code=exc.status_code, content=data)

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content={"message": "Ошибка запроса", "error": str(exc)})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "message": "Ошибка запроса",
                "errors": [{"field": ".".join(map(str, err["loc"])), "reason": err["msg"]} for err in exc.errors()],
            },
        )

    @app.exception_handler(ConnectionError)
    async def connection_error_handler(request: Request, exc: ConnectionError):
        return JSONResponse(status_code=503, content={"message": "Сервис недоступен", "error": str(exc)})

    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError):
        return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"message": f"Не найдено: {str(exc)}"})

    @app.exception_handler(IntegrityError)
    async def duplicate_key_handler(request: Request, exc: IntegrityError):
        return JSONResponse(
            status_code=HTTP_409_CONFLICT, content={"message": "Конфликт данных: сущность уже существует"}
        )

    @app.exception_handler(HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    async def request_too_large_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"message": "Слишком большой запрос", "error": str(exc)},
        )

    @app.exception_handler(HTTP_401_UNAUTHORIZED)
    async def unauthorized_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=HTTP_401_UNAUTHORIZED, content={"message": "Выполните вход в систему", "error": str(exc)}
        )

    @app.exception_handler(HTTP_403_FORBIDDEN)
    async def forbidden_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=HTTP_403_FORBIDDEN, content={"message": "Доступ запрещен", "error": str(exc)})

    @app.exception_handler(HTTP_404_NOT_FOUND)
    async def not_found_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"message": "Не найдено", "error": str(exc)})

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "Internal Server Error", "error": str(exc)}
        )
