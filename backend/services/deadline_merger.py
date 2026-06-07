"""Merger: объединяет данные из двух endpoint'ов, группирует и дедуплицирует.

Алгоритм:
1. Собирает item'ы из calendar и schedule
2. Merge: calendar приоритетнее для дат
3. Group by (lesson_id, type, normalized_title)
4. Merge группы в одно событие
"""

from collections import defaultdict
from datetime import datetime

from backend.services.title_normalizer import detect_sub_type, normalize_title


def _merge_two_items(calendar_item: dict | None, schedule_item: dict | None) -> dict:
    """Объединяет два item'а одного события из разных источников.

    Calendar приоритетнее для дат, schedule приоритетнее для passed-статуса
    (т.к. в schedule поле passed boolean для task/test).
    """
    primary = calendar_item or schedule_item or {}

    # Дата: calendar приоритетнее (точнее)
    date = None
    if calendar_item and calendar_item.get("date"):
        date = calendar_item["date"]
    elif schedule_item and schedule_item.get("date"):
        date = schedule_item["date"]

    # Статус: passed если хоть один passed
    status = "pending"
    cal_status = calendar_item.get("status") if calendar_item else None
    sch_status = schedule_item.get("status") if schedule_item else None

    if cal_status in ("passed", "approved") or sch_status == "passed":
        status = "passed"
    elif cal_status == "approved" or sch_status == "approved":
        status = "approved"

    return {
        "id": primary.get("id"),
        "lesson_id": primary.get("lesson_id"),
        "type": primary.get("type"),
        "title": primary.get("title", ""),
        "date": date,
        "status": status,
        "program_title": primary.get("program_title", "Без названия"),
        "raw": [calendar_item.get("raw") if calendar_item else None,
                schedule_item.get("raw") if schedule_item else None],
    }


def merge_sources(calendar_items: list[dict], schedule_items: list[dict]) -> list[dict]:
    """Объединяет item'ы из двух источников.

    Уникальный ключ для merge: (lesson_id, type, id).
    Если id совпадает — это один и тот же item.
    """
    # Индексируем по id
    by_id: dict[int, dict] = {}

    for item in calendar_items:
        item_id = item.get("id")
        if item_id is not None:
            by_id[item_id] = {"calendar": item, "schedule": None}

    for item in schedule_items:
        item_id = item.get("id")
        if item_id is not None:
            if item_id in by_id:
                by_id[item_id]["schedule"] = item
            else:
                by_id[item_id] = {"calendar": None, "schedule": item}

    # Объединяем
    merged = []
    for parts in by_id.values():
        merged.append(_merge_two_items(parts["calendar"], parts["schedule"]))

    return merged


def group_items(items: list[dict]) -> list[dict]:
    """Группирует item'ы по (lesson_id, type, normalized_title).

    Одна группа = одно событие (с разными вариантами/группами).
    """
    groups: dict[tuple, list[dict]] = defaultdict(list)

    for item in items:
        lesson_id = item.get("lesson_id")
        item_type = item.get("type")
        norm_title = normalize_title(item.get("title", ""))

        if lesson_id is None or not item_type:
            continue

        key = (lesson_id, item_type, norm_title)
        groups[key].append(item)

    result = []
    for (lesson_id, item_type, norm_title), group_items_list in groups.items():
        # Собираем raw items
        raw_items = []
        for g in group_items_list:
            raw = g.get("raw")
            if isinstance(raw, list):
                raw_items.extend([r for r in raw if r is not None])
            elif raw is not None:
                raw_items.append(raw)

        # Дата: минимальная из всех (обычно они совпадают)
        dates = [g["date"] for g in group_items_list if g.get("date")]
        event_date = min(dates) if dates else None

        # Статус: passed если хоть один passed
        statuses = [g.get("status") for g in group_items_list]
        event_status = "pending"
        if "passed" in statuses:
            event_status = "passed"
        elif "approved" in statuses:
            event_status = "approved"

        # Программа: берём первую непустую
        program_title = "Без названия"
        for g in group_items_list:
            pt = g.get("program_title")
            if pt and pt != "Без названия":
                program_title = pt
                break

        # Источник: определяем по наличию данных в calendar / schedule
        sources = set()
        for g in group_items_list:
            raw = g.get("raw")
            if isinstance(raw, list):
                has_calendar = raw[0] is not None
                has_schedule = len(raw) > 1 and raw[1] is not None
                if has_calendar and has_schedule:
                    sources.add("merged")
                elif has_calendar:
                    sources.add("calendar")
                elif has_schedule:
                    sources.add("schedule")
                else:
                    sources.add("calendar")  # fallback
            else:
                sources.add("calendar" if raw is not None else "schedule")
        source = "merged" if len(sources) > 1 else (sources.pop() if sources else "calendar")

        result.append({
            "lesson_id": lesson_id,
            "event_type": item_type,
            "sub_type": detect_sub_type(norm_title, item_type),
            "title": norm_title,
            "program_title": program_title,
            "date": event_date,
            "status": event_status,
            "source": source,
            "raw_items": raw_items,
            "item_count": len(group_items_list),
        })

    return result


def build_deadline_events(calendar_items: list[dict], schedule_items: list[dict]) -> list[dict]:
    """Полный pipeline: merge sources → group → return events.

    Args:
        calendar_items: Результат NetologyCalendarService.fetch_calendar().
        schedule_items: Результат NetologyScheduleService.fetch_schedules().

    Returns:
        Список сгруппированных событий, готовых для сохранения в БД.
    """
    merged = merge_sources(calendar_items, schedule_items)
    grouped = group_items(merged)

    # Сортируем по дате (ближайшие сверху)
    grouped.sort(key=lambda e: (e["date"] is None, e["date"] or datetime.max))

    return grouped
