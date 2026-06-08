"""Сервис для работы с календарём v2.0.

Группировка событий по дням для месячной и недельной сетки.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.deadline_event import DeadlineEvent


# Цветовая кодировка по типу события
_EVENT_COLORS = {
    ("webinar", "lesson"): "#3b82f6",       # синий
    ("webinar", "consultation"): "#8b5cf6", # фиолетовый
    ("webinar", "credit"): "#ef4444",       # красный
    ("webinar", "exam"): "#ef4444",         # красный
    ("task", "task"): "#f97316",            # оранжевый
    ("test", "test"): "#eab308",            # жёлтый
}

_DEFAULT_COLOR = "#6b7280"  # серый


def _event_color(event: DeadlineEvent) -> str:
    """Возвращает hex-цвет для события."""
    return _EVENT_COLORS.get((event.event_type, event.sub_type), _DEFAULT_COLOR)


def _event_time_str(event: DeadlineEvent) -> str | None:
    """Возвращает строку времени начала или None."""
    if event.event_time:
        return event.event_time.strftime("%H:%M")
    return None


def _item_count(event: DeadlineEvent) -> int:
    """Количество уникальных id в raw_items."""
    if not event.raw_items:
        return 1
    unique_ids = {
        item.get("id")
        for item in event.raw_items
        if item.get("id") is not None
    }
    return len(unique_ids) or 1


class CalendarService:
    """Управляет календарём: группировка по дням, месяцам, неделям."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _build_base_stmt(self, user_id, filter_type: str = "all"):
        """Строит базовый SELECT с фильтрами (без ограничения по дате)."""
        stmt = select(DeadlineEvent).where(DeadlineEvent.user_id == user_id)

        if filter_type == "lessons":
            stmt = stmt.where(
                DeadlineEvent.event_type == "webinar",
                DeadlineEvent.sub_type.in_(["lesson", "consultation"]),
            )
        elif filter_type == "works":
            stmt = stmt.where(DeadlineEvent.event_type.in_(["task", "test"]))
        elif filter_type == "control":
            stmt = stmt.where(
                DeadlineEvent.event_type == "webinar",
                DeadlineEvent.sub_type.in_(["credit", "exam"]),
            )

        return stmt

    async def get_month(
        self,
        user_id,
        year: int,
        month: int,
        filter_type: str = "all",
    ) -> dict:
        """Возвращает события за месяц, сгруппированные по дням.

        Returns:
            dict: { year, month, filter, days: { "YYYY-MM-DD": [events] }, total }
        """
        # Диапазон дат
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        stmt = (
            self._build_base_stmt(user_id, filter_type)
            .where(DeadlineEvent.event_date >= start_date)
            .where(DeadlineEvent.event_date < end_date)
            .order_by(DeadlineEvent.event_date.asc(), DeadlineEvent.event_time.asc())
        )

        result = await self.db.execute(stmt)
        events = result.scalars().all()

        days: dict[str, list[dict]] = defaultdict(list)
        total = 0

        for e in events:
            day_key = e.event_date.isoformat() if e.event_date else "no-date"
            days[day_key].append(self._serialize_event(e))
            total += 1

        return {
            "year": year,
            "month": month,
            "filter": filter_type,
            "days": dict(days),
            "total": total,
        }

    async def get_week(
        self,
        user_id,
        year: int,
        week: int,
        filter_type: str = "all",
    ) -> dict:
        """Возвращает события за ISO-неделю, сгруппированные по дням.

        Returns:
            dict: { year, week, filter, days: { "YYYY-MM-DD": [events] }, total }
        """
        # ISO week → дата понедельника
        monday = datetime.strptime(f"{year}-W{week:02d}-1", "%G-W%V-%u").date()
        sunday = monday + timedelta(days=6)

        stmt = (
            self._build_base_stmt(user_id, filter_type)
            .where(DeadlineEvent.event_date >= monday)
            .where(DeadlineEvent.event_date <= sunday)
            .order_by(DeadlineEvent.event_date.asc(), DeadlineEvent.event_time.asc())
        )

        result = await self.db.execute(stmt)
        events = result.scalars().all()

        days: dict[str, list[dict]] = defaultdict(list)
        total = 0

        for e in events:
            day_key = e.event_date.isoformat() if e.event_date else "no-date"
            days[day_key].append(self._serialize_event(e))
            total += 1

        return {
            "year": year,
            "week": week,
            "filter": filter_type,
            "days": dict(days),
            "total": total,
        }

    def _serialize_event(self, event: DeadlineEvent) -> dict:
        """Сериализует DeadlineEvent в dict для CalendarEventResponse."""
        return {
            "id": str(event.id),
            "event_type": event.event_type,
            "sub_type": event.sub_type,
            "title": event.title,
            "program_title": event.program_title,
            "event_date": event.event_date.isoformat() if event.event_date else None,
            "status": event.status,
            "source": event.source,
            "color": _event_color(event),
            "time_str": _event_time_str(event),
            "item_count": _item_count(event),
        }
