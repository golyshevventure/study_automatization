"""Нормализация названий событий и определение подтипов.

Чистые функции без зависимостей от БД или HTTP.
"""

import re

# Регулярки для нормализации title
_VARIANT_RE = re.compile(r"\.\s*Вариант\s*[\w№]+", re.IGNORECASE)
_ATTEMPT_RE = re.compile(r"\.\s*Попытка\s*[\w№]+", re.IGNORECASE)
_GROUP_RE = re.compile(r"[\.\s]*\d+\s*группа", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    """Убирает суффиксы групп, вариантов, попыток из названия.

    Примеры:
        "Тест на зачет. Вариант 1"       -> "Тест на зачет"
        "Тест на зачёт. Попытка №1"      -> "Тест на зачёт"
        "Зачёт. Иностранный язык. 1 группа" -> "Зачёт. Иностранный язык"
        "Иностранный язык 2 группа"      -> "Иностранный язык"
    """
    title = _VARIANT_RE.sub("", title)
    title = _ATTEMPT_RE.sub("", title)
    title = _GROUP_RE.sub("", title)
    title = _WHITESPACE_RE.sub(" ", title)
    title = title.strip(". ")
    return title


def detect_sub_type(title: str, event_type: str) -> str:
    """Определяет подтип события по ключевым словам в названии.

    API Netology возвращает type="webinar" для зачётов, экзаменов,
    консультаций и обычных вебинаров. Мы определяем подтип по title.

    Args:
        title: Название события.
        event_type: Тип из API (task / test / webinar).

    Returns:
        "lesson" | "consultation" | "credit" | "exam"
    """
    if event_type != "webinar":
        return "lesson"

    title_lower = title.lower()

    # Консультация проверяем первой — "Консультация перед экзаменом"
    if "консультация" in title_lower:
        return "consultation"
    if "экзамен" in title_lower:
        return "exam"
    if "зачёт" in title_lower or "зачет" in title_lower:
        return "credit"

    return "lesson"
