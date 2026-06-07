"""Тесты для модуля deadline_merger.

Проверяем:
- merge_sources: объединение item'ов из двух источников
- group_items: группировка по lesson_id
- detect_sub_type: определение подтипа по title
- normalize_title: нормализация названий
"""

from datetime import datetime, timezone

import pytest

from backend.services.deadline_merger import build_deadline_events, group_items, merge_sources
from backend.services.title_normalizer import detect_sub_type, normalize_title


def make_item(id_, lesson_id, type_, title, date=None, status="pending", program="Test"):
    return {
        "id": id_,
        "lesson_id": lesson_id,
        "type": type_,
        "title": title,
        "date": date,
        "status": status,
        "program_title": program,
        "raw": {"id": id_, "title": title},
    }


class TestNormalizeTitle:
    def test_variant_suffix(self):
        assert normalize_title("Тест. Вариант 1") == "Тест"
        assert normalize_title("Тест. Вариант №2") == "Тест"

    def test_attempt_suffix(self):
        assert normalize_title("Тест. Попытка №1") == "Тест"
        assert normalize_title("Тест. Попытка 2") == "Тест"

    def test_group_suffix(self):
        assert normalize_title("Зачёт. Иностранный язык. 1 группа") == "Зачёт. Иностранный язык"
        assert normalize_title("Иностранный язык 2 группа") == "Иностранный язык"

    def test_no_change(self):
        assert normalize_title("Экономическая теория") == "Экономическая теория"


class TestDetectSubType:
    def test_exam(self):
        assert detect_sub_type("Экзамен. Философия", "webinar") == "exam"

    def test_credit(self):
        assert detect_sub_type("Зачёт. Политология", "webinar") == "credit"
        assert detect_sub_type("Зачет. Политология", "webinar") == "credit"

    def test_consultation(self):
        assert detect_sub_type("Консультация перед экзаменом", "webinar") == "consultation"

    def test_lesson(self):
        assert detect_sub_type("Экономическая теория", "webinar") == "lesson"

    def test_non_webinar(self):
        assert detect_sub_type("Тест на зачёт", "test") == "lesson"


class TestMergeSources:
    def test_merge_same_id(self):
        cal = [make_item(1, 100, "task", "ДЗ 1", datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc))]
        sch = [make_item(1, 100, "task", "ДЗ 1 (до 10.06.2026)", datetime(2026, 6, 10, 23, 59, tzinfo=timezone.utc))]

        merged = merge_sources(cal, sch)

        assert len(merged) == 1
        # Дата из calendar (приоритетнее)
        assert merged[0]["date"] == datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc)

    def test_merge_unique_items(self):
        cal = [make_item(1, 100, "webinar", "Вебинар")]
        sch = [make_item(2, 200, "test", "Тест")]

        merged = merge_sources(cal, sch)

        assert len(merged) == 2


class TestGroupItems:
    def test_group_by_lesson_id(self):
        items = [
            make_item(1, 100, "webinar", "Зачёт. Иностранный язык. 1 группа"),
            make_item(2, 100, "webinar", "Зачёт. Иностранный язык. 2 группа"),
        ]

        groups = group_items(items)

        assert len(groups) == 1
        assert groups[0]["title"] == "Зачёт. Иностранный язык"
        assert groups[0]["item_count"] == 2

    def test_group_test_variants(self):
        items = [
            make_item(1, 100, "test", "Тест на зачет. Вариант 1"),
            make_item(2, 100, "test", "Тест на зачет. Вариант 2"),
        ]

        groups = group_items(items)

        assert len(groups) == 1
        assert groups[0]["title"] == "Тест на зачет"
        assert groups[0]["event_type"] == "test"

    def test_no_group_different_lessons(self):
        items = [
            make_item(1, 100, "webinar", "Вебинар 1"),
            make_item(2, 200, "webinar", "Вебинар 2"),
        ]

        groups = group_items(items)

        assert len(groups) == 2

    def test_status_passed_if_any_passed(self):
        items = [
            make_item(1, 100, "test", "Тест. Вариант 1", status="passed"),
            make_item(2, 100, "test", "Тест. Вариант 2", status="pending"),
        ]

        groups = group_items(items)

        assert groups[0]["status"] == "passed"


class TestBuildDeadlineEvents:
    def test_full_pipeline(self):
        cal = [
            make_item(1, 100, "webinar", "Зачёт. Иностранный язык. 1 группа",
                      datetime(2026, 6, 9, 11, 0, tzinfo=timezone.utc), "approved"),
            make_item(2, 100, "webinar", "Зачёт. Иностранный язык. 2 группа",
                      datetime(2026, 6, 9, 12, 40, tzinfo=timezone.utc), "approved"),
        ]
        sch = [
            make_item(3, 100, "test", "Тест на зачет. Вариант 1",
                      datetime(2026, 6, 9, 23, 59, tzinfo=timezone.utc)),
            make_item(4, 100, "test", "Тест на зачет. Вариант 2",
                      datetime(2026, 6, 9, 23, 59, tzinfo=timezone.utc)),
        ]

        events = build_deadline_events(cal, sch)

        # 2 группы: (lesson_id=100, webinar) + (lesson_id=100, test)
        assert len(events) == 2

        # Проверим группу webinar
        web = next(e for e in events if e["event_type"] == "webinar")
        assert web["title"] == "Зачёт. Иностранный язык"
        assert web["sub_type"] == "credit"
        assert web["item_count"] == 2
        assert web["status"] == "passed"

        # Проверим группу test
        tst = next(e for e in events if e["event_type"] == "test")
        assert tst["title"] == "Тест на зачет"
        assert tst["item_count"] == 2
