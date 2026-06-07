"""Сервис для работы с дедлайнами в БД.

CRUD + синхронизация с Netology API.
"""

import hashlib
import time
import uuid as std_uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.deadline_event import DeadlineEvent, DeadlineSyncLog
from backend.services.deadline_merger import build_deadline_events
from backend.services.netology_calendar_service import NetologyCalendarService
from backend.services.netology_schedule_service import NetologyScheduleService


class DeadlineService:
    """Управляет дедлайнами: синхронизация, чтение, фильтрация."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync(self, user_id, cookies: dict) -> dict:
        """Синхронизирует дедлайны с Netology API и сохраняет в БД.

        Args:
            user_id: UUID пользователя.
            cookies: Cookies сессии Netology.

        Returns:
            dict: { synced: int, duration_ms: int, message: str }
        """
        start = time.time()

        # 1. Запрашиваем оба источника
        cal_service = NetologyCalendarService()
        sch_service = NetologyScheduleService()

        cal_items = cal_service.fetch_calendar(cookies)
        sch_items = sch_service.fetch_schedules(cookies)

        # 2. Merge + group
        events = build_deadline_events(cal_items, sch_items)

        # 3. Удаляем события, которых больше нет в новых данных
        new_keys = {
            (event["lesson_id"], event["event_type"], event["title"])
            for event in events
        }
        if new_keys:
            # Получаем существующие события пользователя
            existing_stmt = select(DeadlineEvent).where(DeadlineEvent.user_id == user_id)
            existing_result = await self.db.execute(existing_stmt)
            existing = existing_result.scalars().all()
            to_delete = [
                e.id for e in existing
                if (e.lesson_id, e.event_type, e.title) not in new_keys
            ]
            if to_delete:
                await self.db.execute(
                    delete(DeadlineEvent).where(DeadlineEvent.id.in_(to_delete))
                )

        # 4. Upsert: INSERT новых / UPDATE существующих
        for event in events:
            stmt = (
                insert(DeadlineEvent)
                .values(
                    id=std_uuid.uuid4(),
                    user_id=user_id,
                    lesson_id=event["lesson_id"],
                    event_type=event["event_type"],
                    sub_type=event["sub_type"],
                    title=event["title"],
                    program_title=event.get("program_title"),
                    event_date=event["date"].date() if event["date"] else None,
                    event_time=(
                        event["date"].time() if event["date"] else None
                    ),
                    status=event["status"],
                    source=event["source"],
                    raw_items=event.get("raw_items", []),
                )
                .on_conflict_do_update(
                    index_elements=["user_id", "lesson_id", "event_type", "title"],
                    set_={
                        "sub_type": event["sub_type"],
                        "program_title": event.get("program_title"),
                        "event_date": event["date"].date() if event["date"] else None,
                        "event_time": event["date"].time() if event["date"] else None,
                        "status": event["status"],
                        "source": event["source"],
                        "raw_items": event.get("raw_items", []),
                        "updated_at": datetime.now(timezone.utc),
                    },
                )
            )
            await self.db.execute(stmt)

        # 5. Обновляем лог синхронизации
        checksum = self._compute_checksum(cal_items, sch_items)
        await self.db.execute(
            insert(DeadlineSyncLog)
            .values(
                user_id=user_id,
                last_sync_at=datetime.now(timezone.utc),
                events_count=len(events),
                source_checksum=checksum,
            )
            .on_conflict_do_update(
                index_elements=["user_id"],
                set_={
                    "last_sync_at": datetime.now(timezone.utc),
                    "events_count": len(events),
                    "source_checksum": checksum,
                },
            )
        )

        await self.db.commit()

        duration_ms = int((time.time() - start) * 1000)
        return {
            "synced": len(events),
            "duration_ms": duration_ms,
            "message": f"Синхронизировано {len(events)} событий",
        }

    def _build_base_stmt(self, user_id, filter_type: str = "all", program: str | None = None):
        """Строит базовый SELECT с фильтрами."""
        from sqlalchemy import func
        now = datetime.now(timezone.utc)

        stmt = (
            select(DeadlineEvent)
            .where(DeadlineEvent.user_id == user_id)
            .where(
                DeadlineEvent.event_date >= now.date()
                if now.time().hour >= 0
                else DeadlineEvent.event_date > now.date()
            )
        )

        # Фильтр по категории
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

        # Фильтр по программе
        if program:
            stmt = stmt.where(DeadlineEvent.program_title.ilike(f"%{program}%"))

        return stmt

    async def list_events(
        self,
        user_id,
        filter_type: str = "all",
        limit: int = 100,
        offset: int = 0,
        program: str | None = None,
    ) -> tuple[list[DeadlineEvent], int]:
        """Возвращает список будущих событий с фильтром и общее количество.

        Args:
            user_id: UUID пользователя.
            filter_type: all | lessons | works | control.
            limit: Лимит записей.
            offset: Смещение.
            program: Фильтр по названию программы (подстрока).

        Returns:
            Кортеж (список DeadlineEvent, общее количество).
        """
        from sqlalchemy import func

        base_stmt = self._build_base_stmt(user_id, filter_type, program)

        # Получаем события
        stmt = base_stmt.order_by(
            DeadlineEvent.event_date.asc(),
            DeadlineEvent.event_time.asc(),
        ).limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        events = result.scalars().all()

        # Считаем total
        count_stmt = (
            select(func.count())
            .select_from(DeadlineEvent)
            .where(DeadlineEvent.user_id == user_id)
            .where(
                DeadlineEvent.event_date >= datetime.now(timezone.utc).date()
            )
        )

        if filter_type == "lessons":
            count_stmt = count_stmt.where(
                DeadlineEvent.event_type == "webinar",
                DeadlineEvent.sub_type.in_(["lesson", "consultation"]),
            )
        elif filter_type == "works":
            count_stmt = count_stmt.where(DeadlineEvent.event_type.in_(["task", "test"]))
        elif filter_type == "control":
            count_stmt = count_stmt.where(
                DeadlineEvent.event_type == "webinar",
                DeadlineEvent.sub_type.in_(["credit", "exam"]),
            )

        if program:
            count_stmt = count_stmt.where(DeadlineEvent.program_title.ilike(f"%{program}%"))

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        return list(events), total

    async def get_event(self, user_id, event_id: str) -> DeadlineEvent | None:
        """Возвращает одно событие по ID."""
        stmt = select(DeadlineEvent).where(
            DeadlineEvent.user_id == user_id,
            DeadlineEvent.id == event_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _compute_checksum(cal_items: list, sch_items: list) -> str:
        """Вычисляет простую контрольную сумму исходных данных."""
        data = f"{len(cal_items)}:{len(sch_items)}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
