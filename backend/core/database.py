"""Подключение к PostgreSQL через SQLAlchemy (async).

Используется asyncpg драйвер для полной асинхронности с FastAPI.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from backend.core.config import settings

# Асинхронный движок PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # True для отладки SQL-запросов
    future=True,
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Базовый класс для моделей
Base = declarative_base()


async def get_db() -> AsyncSession:
    """FastAPI dependency для получения сессии БД.

    Yields:
        AsyncSession: активная транзакция с БД.
    """
    async with AsyncSessionLocal() as session:
        yield session
