"""Сервис для работы со структурой программ Netology."""

import json
from pathlib import Path
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.summary import (
    NetologyLesson,
    NetologyLessonItem,
    NetologyModule,
    NetologyProgram,
)

NETOLOGY_BASE = "https://netology.ru"
API_BASE = f"{NETOLOGY_BASE}/backend/api/user"
COOKIES_FILE = Path("backend/netology_cookies/netology_cookies.json")


def _load_cookies() -> dict:
    if not COOKIES_FILE.exists():
        return {}
    with open(COOKIES_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {c["name"]: c["value"] for c in raw if "name" in c}


def _extract_lessons(schedule: dict) -> list:
    """Извлекает lessons из разных форматов schedule."""
    if not isinstance(schedule, dict):
        return []
    lessons = list(schedule.get("lessons", []))
    for block in schedule.get("blocks", []):
        lessons.extend(block.get("lessons", []))
    if not lessons and "profession_modules" in schedule:
        for mod in schedule.get("profession_modules", []):
            prog = mod.get("program", {})
            lessons.extend(prog.get("lessons", []))
    return lessons


class NetologyProgramService:
    """HTTP-first сервис для получения структуры программ Netology."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cookies = _load_cookies()
        self.client = httpx.AsyncClient(
            cookies=self.cookies,
            follow_redirects=True,
            timeout=httpx.Timeout(30.0),
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
        )

    async def close(self):
        await self.client.aclose()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_user_programs(self) -> list[NetologyProgram]:
        """Возвращает список программ пользователя из БД (или sync из API)."""
        result = await self.db.execute(select(NetologyProgram))
        programs = result.scalars().all()
        if programs:
            return list(programs)
        # Sync from API
        return await self._sync_programs()

    async def get_program_modules(self, program_id: UUID) -> list[NetologyModule]:
        """Возвращает модули программы."""
        result = await self.db.execute(
            select(NetologyModule).where(NetologyModule.program_id == program_id)
        )
        modules = result.scalars().all()
        if modules:
            return list(modules)
        # Try sync
        await self._sync_program_modules(program_id)
        result = await self.db.execute(
            select(NetologyModule).where(NetologyModule.program_id == program_id)
        )
        return list(result.scalars().all())

    async def get_module_webinars(
        self, module_id: UUID, only_with_vtt: bool = True
    ) -> list[NetologyLessonItem]:
        """Возвращает видео/вебинары модуля (только с VTT если only_with_vtt=True)."""
        result = await self.db.execute(
            select(NetologyLessonItem)
            .join(NetologyLesson)
            .where(NetologyLesson.module_id == module_id)
            .where(NetologyLessonItem.item_type.in_(["video", "webinar"]))
        )
        items = list(result.scalars().all())

        if not items:
            # Try sync module lessons + items
            await self._sync_module_items(module_id)
            result = await self.db.execute(
                select(NetologyLessonItem)
                .join(NetologyLesson)
                .where(NetologyLesson.module_id == module_id)
                .where(NetologyLessonItem.item_type.in_(["video", "webinar"]))
            )
            items = list(result.scalars().all())

        if only_with_vtt:
            items = [i for i in items if i.has_vtt]

        return items

    # ------------------------------------------------------------------
    # Sync from Netology API
    # ------------------------------------------------------------------

    async def _sync_programs(self) -> list[NetologyProgram]:
        """Синхронизирует список программ из Netology API."""
        resp = await self.client.get(f"{API_BASE}/programs/calendar/filters")
        resp.raise_for_status()
        raw = resp.json()
        programs = raw.get("programs", []) if isinstance(raw, dict) else raw

        created: list[NetologyProgram] = []
        for prog in programs:
            netology_id = str(prog.get("id", ""))
            if not netology_id:
                continue
            # Check if exists
            existing = await self.db.execute(
                select(NetologyProgram).where(
                    NetologyProgram.netology_id == netology_id
                )
            )
            if existing.scalar_one_or_none():
                continue

            db_prog = NetologyProgram(
                netology_id=netology_id,
                title=prog.get("title", prog.get("name", "Без названия")),
                program_type="profession" if prog.get("is_profession") else "program",
            )
            self.db.add(db_prog)
            created.append(db_prog)

        await self.db.commit()
        return created

    async def _sync_program_modules(self, program_id: UUID) -> None:
        """Синхронизирует модули программы."""
        program = await self.db.get(NetologyProgram, program_id)
        if not program:
            return

        # Try professions/{id}/schedule first
        resp = await self.client.get(
            f"{API_BASE}/professions/{program.netology_id}/schedule"
        )
        if resp.status_code != 200:
            resp = await self.client.get(
                f"{API_BASE}/programs/{program.netology_id}/schedule"
            )
        if resp.status_code != 200:
            return

        schedule = resp.json()
        modules = schedule.get("profession_modules", [])

        for mod in modules:
            mod_prog = mod.get("program", {})
            mod_netology_id = str(mod_prog.get("id", ""))
            if not mod_netology_id:
                continue

            existing = await self.db.execute(
                select(NetologyModule).where(
                    NetologyModule.netology_id == mod_netology_id
                )
            )
            if existing.scalar_one_or_none():
                continue

            db_mod = NetologyModule(
                program_id=program_id,
                netology_id=mod_netology_id,
                title=mod_prog.get("name", "Без названия"),
            )
            self.db.add(db_mod)

        await self.db.commit()

    async def _sync_module_items(self, module_id: UUID) -> None:
        """Синхронизирует занятия и items модуля."""
        module = await self.db.get(NetologyModule, module_id)
        if not module:
            return

        resp = await self.client.get(
            f"{API_BASE}/programs/{module.netology_id}/schedule"
        )
        if resp.status_code != 200:
            return

        schedule = resp.json()
        lessons = _extract_lessons(schedule)

        for lesson in lessons:
            lesson_netology_id = str(lesson.get("id", ""))
            if not lesson_netology_id:
                continue

            existing_lesson = await self.db.execute(
                select(NetologyLesson).where(
                    NetologyLesson.netology_id == lesson_netology_id
                )
            )
            db_lesson = existing_lesson.scalar_one_or_none()
            if not db_lesson:
                db_lesson = NetologyLesson(
                    module_id=module_id,
                    netology_id=lesson_netology_id,
                    title=lesson.get("title", "Без названия"),
                )
                self.db.add(db_lesson)
                await self.db.flush()  # To get db_lesson.id

            for li in lesson.get("lesson_items", []):
                li_netology_id = str(li.get("id", ""))
                if not li_netology_id:
                    continue

                existing_item = await self.db.execute(
                    select(NetologyLessonItem).where(
                        NetologyLessonItem.netology_id == li_netology_id
                    )
                )
                if existing_item.scalar_one_or_none():
                    continue

                db_item = NetologyLessonItem(
                    lesson_id=db_lesson.id,
                    netology_id=li_netology_id,
                    title=li.get("title", "Без названия"),
                    item_type=li.get("type", "unknown"),
                    video_url=li.get("video_url") or None,
                    has_vtt=False,
                )
                self.db.add(db_item)

        await self.db.commit()
