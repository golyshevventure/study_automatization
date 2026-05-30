"""Менеджер сессий пользователей.

CRUD-операции для UserSession в PostgreSQL.
"""

import uuid_utils as uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.models.session import UserSession


class SessionManager:
    """Управляет сессиями пользователей в БД."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_or_update_session(
        self,
        email: str,
        cookies: dict,
    ) -> UserSession:
        """Создать или обновить сессию пользователя.

        Args:
            email: Email от аккаунта Netology.
            cookies: Все cookies из httpx.Cookies (dict-формат).

        Returns:
            UserSession: созданная или обновлённая сессия.
        """
        netology_session = cookies.get("_netology-on-rails_session")

        # Ищем существующую сессию по email
        stmt = select(UserSession).where(UserSession.email == email)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Обновляем cookies
            existing.netology_session = netology_session
            existing.cookies_json = dict(cookies)
            existing.updated_at = datetime.now(timezone.utc)
            existing.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        # Создаём новую сессию
        new_session = UserSession(
            email=email,
            netology_session=netology_session,
            cookies_json=dict(cookies),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS),
        )
        self.db.add(new_session)
        await self.db.commit()
        await self.db.refresh(new_session)
        return new_session

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserSession]:
        """Найти сессию по UUID."""
        stmt = select(UserSession).where(UserSession.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[UserSession]:
        """Найти сессию по email."""
        stmt = select(UserSession).where(UserSession.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_session(self, user_id: uuid.UUID) -> None:
        """Удалить сессию (выход из аккаунта)."""
        stmt = select(UserSession).where(UserSession.user_id == user_id)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        if session:
            await self.db.delete(session)
            await self.db.commit()
