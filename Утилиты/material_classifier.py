import re


# Ключевые слова для классификации
CONSPECT_KEYWORDS = ["вебинар", "лекция"]
INFO_KEYWORDS = [
    "информация о дисциплине",
    "критерии",
    "информация для получения зачета",
    "зачёт",
    "зачет",
    "опрос",
    "силабус",
    "методические указания",
]
MATERIALS_KEYWORDS = [
    "рабочая программа",
    "учебник",
    "пособие",
    "презентация",
    "снип",
    "методические указания",
]
SKIP_KEYWORDS = [
    "домашнее задание",
    "дз",
    "творческое задание",
    "контрольная работа",
    "эссе",
    "тестирование",
    "промежуточная аттестация",
    "итоговая аттестация",
]


def should_skip(title: str, section_name: str) -> bool:
    """
    Проверяет, нужно ли пропустить материал (домашки, контрольные и т.д.).
    """
    text = f"{title} {section_name}".lower()
    return any(kw in text for kw in SKIP_KEYWORDS)


def classify_material(title: str, section_name: str) -> str:
    """
    Классифицирует материал в одну из 3 категорий.
    Возвращает: "конспект" | "учебные_материалы" | "инфо"
    """
    title_lower = title.lower()
    section_lower = section_name.lower()

    # Вебинары и лекции → конспекты (приоритет по разделу)
    if any(kw in section_lower for kw in CONSPECT_KEYWORDS):
        return "конспект"

    # Учебники, презентации, рабочие программы → учебные материалы (приоритет по названию)
    if any(kw in title_lower for kw in MATERIALS_KEYWORDS):
        return "учебные_материалы"

    # Информация по дисциплине → инфо (проверяем раздел)
    if any(kw in section_lower for kw in INFO_KEYWORDS):
        return "инфо"

    # Всё остальное → учебные материалы
    return "учебные_материалы"


def category_folder(category: str) -> str:
    """Возвращает имя папки для категории."""
    mapping = {
        "конспект": "Конспекты",
        "учебные_материалы": "Учебные материалы",
        "инфо": "Информация по дисциплине",
    }
    return mapping.get(category, "Учебные материалы")


def classify_lesson_strategy(lesson_title: str, items: list) -> str:
    """
    Определяет стратегию обработки занятия (lesson).
    
    items — список словарей с ключами 'title', 'text', 'video_url'
    
    Возвращает:
      - "skip" — пропустить занятие целиком
      - "split" — обрабатывать каждый item отдельно
      - "merge_conspect" — объединить все items в один конспект
      - "split_program" — специальный случай "Рабочая программа" (разделить по категориям)
    """
    title_lower = lesson_title.lower()

    # P0: пропускаем домашки, контрольные, экзамены
    if should_skip(lesson_title, lesson_title):
        return "skip"

    # Специальный случай: Рабочая программа дисциплины
    # Содержит PDF программы + критерии → разные категории
    if "рабочая программа дисциплины" in title_lower:
        return "split_program"

    # P1: если хотя бы один item содержит видео → ВЕСЬ lesson = конспект (merge)
    has_video = any(item.get("video_url") for item in items)
    if has_video:
        return "merge_conspect"

    # P2: если название lesson содержит вебинар/лекция → конспект
    if any(kw in title_lower for kw in CONSPECT_KEYWORDS):
        return "merge_conspect"

    # P3: остальные — обрабатываем каждый item отдельно
    return "split"


def classify_item(title: str, section_name: str) -> str:
    """
    Классифицирует ОТДЕЛЬНЫЙ item (используется в split-режиме).
    """
    title_lower = title.lower()
    section_lower = section_name.lower()

    if any(kw in title_lower for kw in INFO_KEYWORDS):
        return "инфо"
    if any(kw in title_lower for kw in MATERIALS_KEYWORDS):
        return "учебные_материалы"
    if any(kw in section_lower for kw in INFO_KEYWORDS):
        return "инфо"
    if any(kw in section_lower for kw in CONSPECT_KEYWORDS):
        return "конспект"
    return "учебные_материалы"
