"""Тесты для классификатора материалов."""

import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "summary", "summary_programs")
)

from material_classifier import (
    classify_material,
    category_folder,
    should_skip,
    classify_lesson_strategy_with_confidence,
    is_structure_page,
)


class TestShouldSkip:
    """Тесты для функции should_skip."""

    def test_skip_test(self):
        assert should_skip("Итоговый тест", "Тема 1") is True

    def test_skip_homework(self):
        assert should_skip("Домашнее задание", "Тема 1") is True

    def test_skip_essay(self):
        assert should_skip("Контрольная работа", "Тема 1") is True

    def test_do_not_skip_lecture(self):
        assert should_skip("Вебинар 1", "Тема 1") is False

    def test_do_not_skip_program(self):
        assert should_skip("Рабочая программа", "Инфо") is False


class TestClassifyMaterial:
    """Тесты для функции classify_material."""

    def test_lecture_is_conspect(self):
        # section_name должен содержать конспектное keyword
        assert classify_material("Материал", "Вебинар 1") == "конспект"
        assert classify_material("Материал", "Лекция 1") == "конспект"

    def test_program_is_educational(self):
        assert classify_material("Рабочая программа", "Инфо") == "учебные_материалы"

    def test_syllabus_is_info(self):
        assert classify_material("Силлабус", "Инфо") == "инфо"

    def test_textbook_is_educational(self):
        assert classify_material("Учебник", "Материалы") == "учебные_материалы"


class TestCategoryFolder:
    """Тесты для функции category_folder."""

    def test_conspect_folder(self):
        assert category_folder("конспект") == "Конспекты"

    def test_info_folder(self):
        assert category_folder("инфо") == "Информация по дисциплине"

    def test_educational_folder(self):
        assert category_folder("учебные_материалы") == "Учебные материалы"


class TestClassifyLessonStrategy:
    """Тесты для стратегии обработки уроков."""

    def test_video_lesson_merge_conspect(self):
        items = [{"video_url": "https://example.com/video"}]
        strategy, confidence = classify_lesson_strategy_with_confidence(
            "Вебинар 1", items
        )
        assert strategy == "merge_conspect"
        assert confidence >= 90

    def test_skip_test(self):
        items = [{}]
        strategy, confidence = classify_lesson_strategy_with_confidence(
            "Задание к вебинару (тест)", items
        )
        assert strategy == "skip"
        assert confidence == 100

    def test_split_program(self):
        items = [{}]
        strategy, confidence = classify_lesson_strategy_with_confidence(
            "Рабочая программа дисциплины", items
        )
        assert strategy == "split_program"
        assert confidence == 100


class TestIsStructurePage:
    """Тесты для определения structure pages."""

    def test_real_structure_page(self):
        text = "Структура и содержание курса. Тема 1: Введение. Тема 2: Основы. Тема 3: Продвинутое."
        assert is_structure_page(text) is True

    def test_normal_content(self):
        text = "Экономическая теория изучает закономерности производства и потребления."
        assert is_structure_page(text) is False

    def test_short_text(self):
        assert is_structure_page("Короткий текст") is False
