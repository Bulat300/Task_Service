import os
import asyncio
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from alembic.config import Config
from alembic import command

from main import app
from src.core.database import get_db
from src.infra.mq.client import MessageQueueClientAsync


@pytest_asyncio.fixture(scope="session", autouse=True)
async def event_loop():
    loop = asyncio.get_event_loop()
    yield loop


@pytest_asyncio.fixture(scope="session")
async def test_db_engine(event_loop):
    dsn = (
        f"postgresql+asyncpg://{os.environ['DB_USER']}:"
        f"{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:"
        f"{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )
    engine = create_async_engine(dsn, echo=False, future=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def apply_migrations(test_db_engine, event_loop):
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option(
        "sqlalchemy.url",
        f"postgresql+asyncpg://{os.environ['DB_USER']}:"
        f"{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:"
        f"{os.environ['DB_PORT']}/{os.environ['DB_NAME']}",
    )

    async with test_db_engine.begin() as conn:
        await conn.run_sync(lambda connection: command.upgrade(alembic_cfg, "head"))
    yield


@pytest_asyncio.fixture(scope="session")
async def test_db_session_maker(test_db_engine):
    maker = async_sessionmaker(bind=test_db_engine, expire_on_commit=False, class_=AsyncSession)
    return maker


@pytest_asyncio.fixture(scope="function")
async def test_db(test_db_session_maker):
    async with test_db_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function", autouse=True)
async def override_get_db_dependency(test_db):
    async def _override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture(scope="session")
async def mq_client():
    client = MessageQueueClientAsync.get_instance()
    await client.configure()
    yield client
    try:
        await client.close()
    except Exception:
        pass


@pytest_asyncio.fixture(scope="session")
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
