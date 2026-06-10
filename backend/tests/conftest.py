"""Pytest fixtures для backend-тестов.

Каждый тест выполняется внутри nested transaction (SAVEPOINT).
Даже если тест делает commit, данные откатываются в teardown.
Тесты НЕ пишут в production БД — все изменения откатываются.
"""

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from backend.core.config import settings
from backend.models.base import Base
import backend.models.session  # noqa: F401 — регистрирует session-модели
import backend.models.deadline_event  # noqa: F401 — регистрирует deadline-модели
import backend.models.summary  # noqa: F401 — регистрирует summary-модели


def get_test_engine():
    """Создаёт новый engine для каждого теста."""
    return create_async_engine(settings.DATABASE_URL, echo=False, future=True)


@pytest_asyncio.fixture(scope="function")
async def db():
    """Асинхронная сессия БД для тестов.

    Стратегия nested transaction:
    1. Создаём соединение
    2. Начинаем внешнюю транзакцию (conn.begin())
    3. Создаём SAVEPOINT (conn.begin_nested())
    4. Сессия работает внутри SAVEPOINT
    5. Тест может делать commit — это закрывает SAVEPOINT, но данные остаются
       во внешней транзакции
    6. Teardown: откатываем внешнюю транзакцию — все данные исчезают
    7. НЕ делаем drop_all — таблицы остаются для production
    """
    engine = get_test_engine()

    # Убеждаемся что таблицы существуют (idempotent)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Сессия внутри nested transaction
    async with engine.connect() as conn:
        trans = await conn.begin()          # внешняя транзакция
        await conn.begin_nested()            # SAVEPOINT для теста

        session_maker = async_sessionmaker(
            conn,
            expire_on_commit=False,
        )
        session = session_maker()

        yield session

        await session.close()
        await trans.rollback()               # откатываем ВСЁ

    await engine.dispose()
