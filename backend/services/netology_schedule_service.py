"""Сервис для получения расписания программ из Netology API.

Использует комбинацию endpoint'ов:
- /programs/{id}/schedule — для обычных курсов
- /professions/{id}/schedule → /programs/{program_id}/schedule — для профессий/бакалавриата
"""

import re
from datetime import datetime, timezone

import httpx

NETOLOGY_BASE = "https://netology.ru"

# Паттерны для парсинга даты из title
# Форматы: "до ДД.ММ.ГГГГ", "Дедлайн ДД.ММ.ГГГГ", "Дедлайн — ДД.ММ", "Дедлайн ДД.ММ"
_DEADLINE_WITH_YEAR_RE = re.compile(
    r"(?:Дедлайн|до)\s*[—–\-]?\s*(\d{1,2})\.(\d{1,2})\.(\d{4})",
    re.IGNORECASE,
)
_DEADLINE_NO_YEAR_RE = re.compile(
    r"(?:Дедлайн|до)\s*[—–\-]?\s*(\d{1,2})\.(\d{1,2})\b",
    re.IGNORECASE,
)


def _parse_deadline_from_title(title: str) -> datetime | None:
    """Парсит дедлайн из названия.

    Поддерживаемые форматы:
        - "до ДД.ММ.ГГГГ"
        - "Дедлайн ДД.ММ.ГГГГ"
        - "Дедлайн — ДД.ММ" (без года — эвристика)
    """
    # Сначала ищем с годом
    match = _DEADLINE_WITH_YEAR_RE.search(title)
    if match:
        day, month, year = match.groups()
        try:
            return datetime(int(year), int(month), int(day), 23, 59, tzinfo=timezone.utc)
        except ValueError:
            return None

    # Пробуем без года
    match = _DEADLINE_NO_YEAR_RE.search(title)
    if not match:
        return None

    day, month = match.groups()
    now = datetime.now(timezone.utc)
    try:
        candidate = datetime(now.year, int(month), int(day), 23, 59, tzinfo=timezone.utc)
    except ValueError:
        return None

    # Эвристика: если дата в прошлом более чем на 30 дней — следующий год
    if (now - candidate).days > 30:
        try:
            candidate = datetime(now.year + 1, int(month), int(day), 23, 59, tzinfo=timezone.utc)
        except ValueError:
            return None

    return candidate


def _extract_schedule_status(item: dict) -> str:
    """Определяет статус из program schedule."""
    passed = item.get("passed")
    if passed is True:
        return "passed"
    return "pending"


class NetologyScheduleService:
    """Получает расписание программ и извлекает task/test/webinar."""

    def __init__(self, timeout: float = 60.0):
        self.timeout = timeout

    def fetch_schedules(self, cookies: dict) -> list[dict]:
        """Запрашивает schedule для всех активных программ/курсов.

        Args:
            cookies: Cookies сессии Netology (dict).

        Returns:
            Список item'ов с единообразными полями.
        """
        program_ids = self._collect_program_ids(cookies)

        result = []
        for prog_id in program_ids:
            try:
                items = self._fetch_single_schedule(prog_id, cookies)
                result.extend(items)
            except (httpx.HTTPStatusError, httpx.ReadTimeout):
                continue

        return result

    def _collect_program_ids(self, cookies: dict) -> set[int]:
        """Собирает все program_id (курсы) из активных программ.

        Логика:
        1. Получаем список активных программ из /calendar/filters.
        2. Для каждой программы пробуем /programs/{id}/schedule.
        3. Если schedule пустой (0 lessons) — пробуем /professions/{id}/schedule
           и извлекаем вложенные курсы.
        """
        url = f"{NETOLOGY_BASE}/backend/api/user/programs/calendar/filters"
        with httpx.Client(timeout=self.timeout, cookies=cookies) as client:
            response = client.get(url)
        response.raise_for_status()
        data = response.json()

        program_ids: set[int] = set()

        for prog in data.get("programs", []):
            prog_id = prog.get("id")
            if not prog_id:
                continue

            # Пробуем как обычный курс
            try:
                has_lessons = self._has_schedule_lessons(prog_id, cookies)
                if has_lessons:
                    program_ids.add(prog_id)
                    continue
            except (httpx.HTTPStatusError, httpx.ReadTimeout):
                pass

            # Если пусто — пробуем как профессию
            try:
                nested = self._get_profession_program_ids(prog_id, cookies)
                program_ids.update(nested)
            except (httpx.HTTPStatusError, httpx.ReadTimeout):
                pass

        return program_ids

    def _has_schedule_lessons(self, program_id: int, cookies: dict) -> bool:
        """Проверяет, есть ли lessons в /programs/{id}/schedule."""
        url = f"{NETOLOGY_BASE}/backend/api/user/programs/{program_id}/schedule"
        with httpx.Client(timeout=self.timeout, cookies=cookies) as client:
            response = client.get(url)
        response.raise_for_status()
        data = response.json()
        return len(data.get("lessons", [])) > 0

    def _get_profession_program_ids(self, profession_id: int, cookies: dict) -> set[int]:
        """Извлекает program_id курсов из profession schedule."""
        url = f"{NETOLOGY_BASE}/backend/api/user/professions/{profession_id}/schedule"
        with httpx.Client(timeout=self.timeout, cookies=cookies) as client:
            response = client.get(url)

        if response.status_code != 200:
            return set()

        data = response.json()
        ids: set[int] = set()

        for pm in data.get("profession_modules", []):
            program = pm.get("program")
            if program and isinstance(program, dict):
                pid = program.get("id")
                if pid:
                    ids.add(pid)

        return ids

    def _fetch_single_schedule(self, program_id: int, cookies: dict) -> list[dict]:
        """Запрашивает schedule одной программы (курса)."""
        url = f"{NETOLOGY_BASE}/backend/api/user/programs/{program_id}/schedule"
        with httpx.Client(timeout=self.timeout, cookies=cookies) as client:
            response = client.get(url)
        response.raise_for_status()
        data = response.json()

        program_title = data.get("title", "Без названия")
        result = []

        for lesson in data.get("lessons", []):
            lesson_id = lesson.get("id")
            for item in lesson.get("lesson_items", []):
                item_type = item.get("type")
                if item_type not in ("task", "test", "webinar"):
                    continue

                # Для task/test парсим дедлайн из title
                if item_type in ("task", "test"):
                    date = _parse_deadline_from_title(item.get("title", ""))
                else:
                    date = None

                result.append({
                    "id": item.get("id"),
                    "lesson_id": lesson_id,
                    "type": item_type,
                    "title": item.get("title", ""),
                    "date": date,
                    "status": _extract_schedule_status(item),
                    "program_title": program_title,
                    "raw": item,
                })

        return result
