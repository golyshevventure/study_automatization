"""Сервис для получения календаря обучения из Netology API.

Endpoint: GET /backend/api/user/student_learning/calendar
Отдаёт: task (ДЗ) + webinar (вебинары, зачёты, экзамены)
"""

from datetime import datetime
from typing import Any

import httpx

NETOLOGY_BASE = "https://netology.ru"
CALENDAR_URL = f"{NETOLOGY_BASE}/backend/api/user/student_learning/calendar"


def _parse_iso_datetime(value: str | None) -> datetime | None:
    """Парсит ISO-строку в datetime."""
    if not value:
        return None
    try:
        # Убираем миллисекунды если нужно
        value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _extract_task_deadline(item: dict) -> datetime | None:
    """Извлекает дедлайн из lesson_task для type='task'."""
    lesson_task = item.get("lesson_task")
    if not lesson_task:
        return None
    deadline = lesson_task.get("deadline")
    return _parse_iso_datetime(deadline)


def _extract_webinar_datetime(item: dict) -> datetime | None:
    """Извлекает дату начала из webinar."""
    return _parse_iso_datetime(item.get("starts_at"))


def _extract_status(item: dict) -> str:
    """Определяет статус элемента."""
    # Для webinar — берём status из API
    status = item.get("status")
    if status in ("passed", "approved"):
        return status

    # Для task — проверяем homework.status
    lesson_task = item.get("lesson_task")
    if lesson_task:
        homework = lesson_task.get("homework", {})
        hw_status = homework.get("status")
        if hw_status == "waiting_review":
            return "approved"

    return "pending"


class NetologyCalendarService:
    """Получает данные из /student_learning/calendar."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def fetch_calendar(self, cookies: dict) -> list[dict]:
        """Запрашивает календарь и возвращает нормализованные item'ы.

        Args:
            cookies: Cookies сессии Netology (dict).

        Returns:
            Список item'ов с единообразными полями:
            - id: int
            - lesson_id: int
            - type: "task" | "webinar"
            - title: str
            - date: datetime | None
            - status: "pending" | "approved" | "passed"
            - program_title: str
            - raw: dict (оригинальный объект)
        """
        with httpx.Client(timeout=self.timeout, cookies=cookies) as client:
            response = client.get(CALENDAR_URL)
        response.raise_for_status()
        data = response.json()

        result = []
        for program in data.get("programs", []):
            program_title = program.get("title", "Без названия")
            for item in program.get("lesson_items", []):
                item_type = item.get("type")
                if item_type not in ("task", "webinar"):
                    continue

                if item_type == "task":
                    date = _extract_task_deadline(item)
                else:
                    date = _extract_webinar_datetime(item)

                result.append({
                    "id": item.get("id"),
                    "lesson_id": item.get("lesson_id"),
                    "type": item_type,
                    "title": item.get("title", ""),
                    "date": date,
                    "status": _extract_status(item),
                    "program_title": program_title,
                    "raw": item,
                })

        return result
