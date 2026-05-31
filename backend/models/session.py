"""Модель сессии пользователя Netology.

Хранит cookies, email и метаданные для последующих запросов к API Netology.
"""

import uuid_utils as uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


def generate_uuid7() -> uuid.UUID:
    """Генерирует UUID v7 — временной + рандомный.

    Быстро индексируется БД, но непредсказуем (не 1, 2, 3...).
    """
    return uuid.uuid7()


class UserSession(Base):
    """Таблица сессий пользователей.

    Каждая запись соответствует одному авторизованному пользователю Netology.
    """

    __tablename__ = "user_sessions"

    # UUID v7 — непредсказуемый, но оптимальный для индексов
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid7,
    )

    # Email пользователя (уникальный, для быстрого поиска)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Основная сессия Netology (cookie _netology-on-rails_session)
    netology_session: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Все cookies от Netology в формате JSON
    cookies_json: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Профиль пользователя (из Netology, кешируется при логине)
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Кэш данных программ (чтобы не ддосить Netology)
    programs_cache_json: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    programs_cached_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Метаданные
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<UserSession user_id={self.user_id} email={self.email}>"
