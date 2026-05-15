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
