import re


# =============================================================================
# KEYWORD LISTS
# =============================================================================

CONSPECT_KEYWORDS = [
    "вебинар",
    "лекция",
    "итоги темы",
    "заключение",
]

INFO_KEYWORDS = [
    "информация о дисциплине",
    "критерии",
    "информация для получения зачета",
    "зачёт",
    "зачет",
    "опрос",
    "силлабус",
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
    "тест",
    "промежуточная аттестация",
    "итоговая аттестация",
    "итоговый тест",
    "задание к вебинару",
    "задание к лекции",
]

# Negative keywords — if these are present, we should NOT treat as conspect
# even if CONSPECT_KEYWORDS match (e.g. "задание к вебинару" contains "вебинар")
NEGATIVE_KEYWORDS = [
    "задание к вебинару",
    "задание к лекции",
    "тест",
    "домашнее задание",
    "контрольная",
    "эссе",
]

# Patterns that strongly indicate a course structure / syllabus page
STRUCTURE_PAGE_PATTERNS = [
    "структура и содержание курса",
    "тематический план",
    "программа дисциплины",
    "цели и задачи дисциплины",
    "цели и задачи",
]


# =============================================================================
# SKIP CHECK
# =============================================================================

def should_skip(title: str, section_name: str) -> bool:
    """
    Проверяет, нужно ли пропустить материал (домашки, контрольные, тесты и т.д.).
    """
    text = f"{title} {section_name}".lower()
    return any(kw in text for kw in SKIP_KEYWORDS)


# =============================================================================
# PER-ITEM CLASSIFICATION (split mode)
# =============================================================================

def classify_material(title: str, section_name: str) -> str:
    """
    Классифицирует материал в одну из 3 категорий.
    Возвращает: "конспект" | "учебные_материалы" | "инфо"
    """
    title_lower = title.lower()
    section_lower = section_name.lower()

    # P0: skip-negative — if title contains negative keywords, treat as info/materials
    if any(kw in title_lower for kw in NEGATIVE_KEYWORDS):
        # Тесты/задания → не конспекты
        pass  # fall through to other checks
    else:
        # Вебинары и лекции → конспекты (приоритет по разделу)
        if any(kw in section_lower for kw in CONSPECT_KEYWORDS):
            return "конспект"

    # Учебники, презентации, рабочие программы → учебные материалы (приоритет по названию)
    if any(kw in title_lower for kw in MATERIALS_KEYWORDS):
        return "учебные_материалы"

    # Информация по дисциплине → инфо (проверяем и раздел, и название)
    if any(kw in section_lower for kw in INFO_KEYWORDS):
        return "инфо"
    if any(kw in title_lower for kw in INFO_KEYWORDS):
        return "инфо"

    # Всё остальное → учебные материалы
    return "учебные_материалы"


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
        # Negative check: don't classify as conspect if it's a test/assignment
        if not any(kw in title_lower for kw in NEGATIVE_KEYWORDS):
            return "конспект"
    return "учебные_материалы"


def category_folder(category: str) -> str:
    """Возвращает имя папки для категории."""
    mapping = {
        "конспект": "Конспекты",
        "учебные_материалы": "Учебные материалы",
        "инфо": "Информация по дисциплине",
    }
    return mapping.get(category, "Учебные материалы")


# =============================================================================
# LESSON-LEVEL STRATEGY
# =============================================================================

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

    # P0: пропускаем домашки, контрольные, экзамены, тесты
    if should_skip(lesson_title, lesson_title):
        return "skip"

    # Специальный случай: Рабочая программа дисциплины
    if "рабочая программа дисциплины" in title_lower:
        return "split_program"

    # P1: если хотя бы один item содержит видео → ВЕСЬ lesson = конспект (merge)
    has_video = any(item.get("video_url") for item in items)
    if has_video:
        # But double-check it's not a test/assignment with a video preview
        if not any(kw in title_lower for kw in NEGATIVE_KEYWORDS):
            return "merge_conspect"

    # P2: если название lesson содержит вебинар/лекция → конспект
    # BUT: check negative keywords first (e.g. "задание к вебинару" contains "вебинар")
    if any(kw in title_lower for kw in CONSPECT_KEYWORDS):
        if not any(kw in title_lower for kw in NEGATIVE_KEYWORDS):
            return "merge_conspect"

    # P3: остальные — обрабатываем каждый item отдельно
    return "split"


def classify_lesson_strategy_with_confidence(lesson_title: str, items: list) -> tuple:
    """
    Keyword-based strategy with confidence score (0–100).

    Returns (strategy, confidence).
    Confidence levels:
      - 100: exact match (skip keywords, рабочая программа)
      - 90:  strong match (has_video + no negative keywords)
      - 70:  moderate match (conspect keywords + no negative keywords)
      - 50:  weak match (split — default)
      - 30:  uncertain (has video BUT negative keywords present)
    """
    title_lower = lesson_title.lower()

    # P0: skip — 100% confidence
    if should_skip(lesson_title, lesson_title):
        return "skip", 100

    # Special: рабочая программа — 100% confidence
    if "рабочая программа дисциплины" in title_lower:
        return "split_program", 100

    # Check negative keywords presence
    has_negative = any(kw in title_lower for kw in NEGATIVE_KEYWORDS)
    has_video = any(item.get("video_url") for item in items)

    # P1: video present — usually conspect, unless negative keywords
    if has_video:
        if not has_negative:
            return "merge_conspect", 90
        else:
            # Video exists but title says "тест" / "задание" — uncertain
            return "skip", 30

    # P2: conspect keywords — moderate confidence unless negative
    if any(kw in title_lower for kw in CONSPECT_KEYWORDS):
        if not has_negative:
            return "merge_conspect", 70
        else:
            # "вебинар" in "задание к вебинару" — uncertain
            return "skip", 50

    # P3: default split — weak confidence, might need LLM fallback
    return "split", 50


# =============================================================================
# STRUCTURE PAGE DETECTION
# =============================================================================

def is_structure_page(text: str) -> bool:
    """
    Определяет, является ли текст HTML fallback'ом описанием программы курса
    вместо реального контента (вебинара, лекции и т.д.).
    """
    if not text:
        return False
    text_lower = text.lower()
    # Count how many structure patterns match
    matches = sum(1 for pat in STRUCTURE_PAGE_PATTERNS if pat in text_lower)
    # If 2+ patterns match → very likely a structure page
    if matches >= 2:
        return True
    # If 1 strong pattern + mentions multiple "Тема N:" → likely structure
    if matches >= 1:
        # Count "тема" mentions with numbers
        topic_refs = len(re.findall(r'тема\s*\d+[\.:\)]', text_lower))
        if topic_refs >= 3:
            return True
    return False
