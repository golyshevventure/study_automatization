"""Pydantic-схемы для модуля «Календарь v2.0»."""

from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field


class CalendarEventResponse(BaseModel):
    """Событие в календаре (один день)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    sub_type: str
    title: str
    program_title: str | None
    event_date: date | None
    status: str
    source: str
    raw_items: list[dict[str, Any]] | None = Field(default=None, exclude=True)

    # Дополнительные поля для календаря
    color: str = Field(default="#3b82f6", description="Hex-цвет события")
    time_str: str | None = Field(default=None, description="Время начала, если есть")
    item_count: int = Field(default=1, description="Количество вариантов/групп")


class CalendarMonthResponse(BaseModel):
    """Ответ /calendar/month — события за месяц, сгруппированные по дням."""

    year: int
    month: int
    filter: str
    days: dict[str, list[CalendarEventResponse]]
    total: int


class CalendarWeekResponse(BaseModel):
    """Ответ /calendar/week — события за неделю (ISO), сгруппированные по дням."""

    year: int
    week: int
    filter: str
    days: dict[str, list[CalendarEventResponse]]
    total: int
