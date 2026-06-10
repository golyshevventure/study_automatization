"""Pytest fixtures для backend-тестов."""

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.core.config import settings
from backend.models.base import Base
import backend.models.summary  # noqa: F401 — регистрирует summary-модели


def get_test_engine():
    """Создаёт новый engine для каждого теста."""
    return create_async_engine(settings.DATABASE_URL, echo=False, future=True)


@pytest_asyncio.fixture(scope="function")
async def db():
    """Асинхронная сессия БД для тестов.

    Каждый тест получает свежий engine и сессию,
    чтобы избежать конфликтов event loop с asyncpg.
    """
    engine = get_test_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
        await session.rollback()

    await engine.dispose()
