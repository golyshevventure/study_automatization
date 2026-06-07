"""Pydantic-схемы для модуля «Ближайшие события и дедлайны»."""

from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


class DeadlineEventResponse(BaseModel):
    """Сгруппированное событие (ответ API)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    sub_type: str
    title: str
    program_title: str | None
    event_date: date | None
    event_time: time | None
    status: str
    source: str
    raw_items: list[dict[str, Any]] | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def item_count(self) -> int:
        return len(self.raw_items) if self.raw_items else 1


class DeadlineEventDetailResponse(DeadlineEventResponse):
    """Детали события с raw_items."""

    # Переопределяем raw_items чтобы включить его в сериализацию
    raw_items: list[dict[str, Any]] | None = Field(default=None, exclude=False)


class DeadlineSyncResponse(BaseModel):
    """Результат синхронизации."""

    synced: int
    duration_ms: int
    message: str


class DeadlineListResponse(BaseModel):
    """Список событий."""

    events: list[DeadlineEventResponse]
    total: int
    filter: str


class DeadlineFilter(str):
    """Доступные фильтры."""

    LESSONS = "lessons"
    WORKS = "works"
    CONTROL = "control"
    ALL = "all"
