"""Тесты SessionService.

Проверяют создание, получение и удаление сессий.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import settings
from backend.models.base import Base
from backend.services.session_service.session_manager import SessionManager


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


@pytest.mark.asyncio
async def test_create_session(db: AsyncSession):
    """Создание новой сессии."""
    manager = SessionManager(db)
    cookies = {"_netology-on-rails_session": "test-session-123"}
    session = await manager.create_or_update_session(
        email="test@example.com",
        cookies=cookies,
    )
    assert session.email == "test@example.com"
    assert session.netology_session == "test-session-123"
    assert session.cookies_json == cookies
    assert session.user_id is not None


@pytest.mark.asyncio
async def test_update_existing_session(db: AsyncSession):
    """Обновление существующей сессии."""
    manager = SessionManager(db)
    cookies1 = {"_netology-on-rails_session": "session-old"}
    session1 = await manager.create_or_update_session(
        email="update@example.com",
        cookies=cookies1,
    )
    user_id = session1.user_id

    cookies2 = {"_netology-on-rails_session": "session-new"}
    session2 = await manager.create_or_update_session(
        email="update@example.com",
        cookies=cookies2,
    )
    assert session2.user_id == user_id
    assert session2.netology_session == "session-new"


@pytest.mark.asyncio
async def test_get_by_user_id(db: AsyncSession):
    """Поиск сессии по user_id."""
    manager = SessionManager(db)
    cookies = {"_netology-on-rails_session": "test"}
    created = await manager.create_or_update_session(
        email="find@example.com",
        cookies=cookies,
    )
    found = await manager.get_by_user_id(created.user_id)
    assert found is not None
    assert found.email == "find@example.com"


@pytest.mark.asyncio
async def test_delete_session(db: AsyncSession):
    """Удаление сессии."""
    manager = SessionManager(db)
    cookies = {"_netology-on-rails_session": "del"}
    session = await manager.create_or_update_session(
        email="del@example.com",
        cookies=cookies,
    )
    await manager.delete_session(session.user_id)
    found = await manager.get_by_user_id(session.user_id)
    assert found is None
