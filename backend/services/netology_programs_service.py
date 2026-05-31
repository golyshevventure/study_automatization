"""Сервис для получения активных программ с Netology.

Использует комбинацию endpoint'ов:
- /programs/calendar/filters — достоверный список активных программ
- /programs/progress — прогресс по всем программам (только для подтверждённых id)
"""

import httpx

NETOLOGY_BASE = "https://netology.ru"


def _calc_progress(passed: int, total: int) -> int:
    """Вычислить процент прогресса."""
    if total <= 0:
        return 0
    return int(round(passed / total * 100))


def _module_progress(module: dict) -> int:
    """Прогресс модуля из lesson_items."""
    return _calc_progress(
        module.get("lesson_items_passed", 0),
        module.get("lesson_items_count", 0),
    )


def _program_progress(program: dict) -> int:
    """Прогресс программы = суммарный прогресс по lesson_items всех модулей."""
    modules = program.get("modules", [])
    total_passed = sum(m.get("lesson_items_passed", 0) for m in modules)
    total_count = sum(m.get("lesson_items_count", 0) for m in modules)
    return _calc_progress(total_passed, total_count)


class NetologyProgramsService:
    """Получает активные программы пользователя с прогрессом."""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    def get_active_courses(self, cookies: dict) -> list[dict]:
        """Вернуть список активных курсов с прогрессом.

        Args:
            cookies: Cookies сессии Netology (dict).

        Returns:
            Список курсов с полями: id, title, type, progress, passed, modules.
        """
        active_ids = self._get_active_program_ids(cookies)
        progress_map = self._get_progress_map(cookies)

        result = []
        for prog_id in active_ids:
            progress_data = progress_map.get(prog_id, {})
            is_profession = progress_data.get("is_profession", False)
            progress = _program_progress(progress_data)

            raw_modules = progress_data.get("modules", [])

            if is_profession:
                modules = []
                for m in raw_modules:
                    path = m.get("program_schedule_path", "")
                    link = f"{NETOLOGY_BASE}{path}" if path else None
                    modules.append({
                        "title": m.get("title", "Без названия"),
                        "progress": _module_progress(m),
                        "link": link,
                    })
            else:
                # Для обычных курсов показываем один модуль — сам курс
                path = raw_modules[0].get("program_schedule_path", "") if raw_modules else ""
                link = f"{NETOLOGY_BASE}{path}" if path else None
                modules = [{
                    "title": progress_data.get("title", "Без названия"),
                    "progress": progress,
                    "link": link,
                }]

            result.append({
                "id": prog_id,
                "title": progress_data.get("title", "Без названия"),
                "type": "Профессия" if is_profession else "Курс",
                "progress": progress,
                "passed": progress == 100,
                "modules": modules,
            })

        result.sort(
            key=lambda c: (
                -int(c["type"] == "Профессия"),
                -c["progress"],
            )
        )
        return result

    def _get_active_program_ids(self, cookies: dict) -> set[int]:
        """Получить id активных программ из /calendar/filters."""
        url = f"{NETOLOGY_BASE}/backend/api/user/programs/calendar/filters"
        with httpx.Client(timeout=self.timeout, cookies=cookies) as client:
            response = client.get(url)
        response.raise_for_status()
        data = response.json()
        return {p["id"] for p in data.get("programs", [])}

    def _get_progress_map(self, cookies: dict) -> dict[int, dict]:
        """Получить мапу прогресса из /programs/progress."""
        url = f"{NETOLOGY_BASE}/backend/api/user/programs/progress"
        with httpx.Client(timeout=self.timeout, cookies=cookies) as client:
            response = client.get(url)
        response.raise_for_status()
        data = response.json()
        return {p["id"]: p for p in data.get("programs", [])}
