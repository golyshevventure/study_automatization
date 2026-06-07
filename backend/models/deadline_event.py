"""Модели для модуля «Ближайшие события и дедлайны»."""

import uuid_utils as uuid
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Time, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


def generate_uuid7() -> uuid.UUID:
    """Генерирует UUID v7 — временной + рандомный."""
    return uuid.uuid7()


class DeadlineEvent(Base):
    """Сгруппированные события (дедлайны, зачёты, экзамены, занятия).

    Хранит результат merge + group из двух endpoint'ов Netology API.
    Одна запись = одна группа item'ов с одинаковым lesson_id.
    """

    __tablename__ = "deadline_events"

    # UUID v7 — оптимальный для индексов
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid7,
    )

    # Связь с пользователем
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_sessions.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Группировочный ключ из API Netology
    lesson_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Тип события из API: task / test / webinar
    event_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    # Подтип (для webinar): lesson / consultation / credit / exam
    sub_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="lesson",
        index=True,
    )

    # Нормализованное название (без «Вариант 1», «2 группа»)
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Название программы / модуля
    program_title: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Дата события (дедлайн или дата начала вебинара)
    event_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    # Время начала (только для webinar)
    event_time: Mapped[Optional[time]] = mapped_column(
        Time,
        nullable=True,
    )

    # Статус: pending / approved / passed / overdue
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    # Источник: calendar / schedule / merged
    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="merged",
    )

    # Сырые item'ы группы (для детализации в календаре)
    raw_items: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
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

    def __repr__(self) -> str:
        return (
            f"<DeadlineEvent {self.title} ({self.event_type}) "
            f"date={self.event_date} status={self.status}>"
        )


class DeadlineSyncLog(Base):
    """Лог последней синхронизации дедлайнов для пользователя."""

    __tablename__ = "deadline_sync_log"

    # Связь с пользователем (1:1)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_sessions.user_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Время последней синхронизации
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Количество событий после последней синхронизации
    events_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Контрольная сумма исходных данных (для определения изменений)
    source_checksum: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<DeadlineSyncLog user={self.user_id} "
            f"synced_at={self.last_sync_at} events={self.events_count}>"
        )
