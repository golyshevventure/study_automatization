"""Интеграционные тесты API модуля Summary."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.models.summary import (
    Conspect,
    ConspectJob,
    NetologyLesson,
    NetologyLessonItem,
    NetologyModule,
    NetologyProgram,
)

client = TestClient(app)
TEST_USER_ID = "019e788c-8dd1-7e02-8752-9812841d98bd"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def seed_program(db: AsyncSession):
    """Создать тестовую программу с модулем, уроком и вебинаром."""
    import uuid_utils as uuid

    program = NetologyProgram(
        id=uuid.uuid7(),
        user_id=uuid.UUID(TEST_USER_ID),
        netology_id="prog-123",
        title="Test Program",
        program_type="program",
    )
    db.add(program)
    await db.flush()

    module = NetologyModule(
        id=uuid.uuid7(),
        program_id=program.id,
        netology_id="mod-123",
        title="Test Module",
    )
    db.add(module)
    await db.flush()

    lesson = NetologyLesson(
        id=uuid.uuid7(),
        module_id=module.id,
        netology_id="lesson-123",
        title="Test Lesson",
    )
    db.add(lesson)
    await db.flush()

    item = NetologyLessonItem(
        id=uuid.uuid7(),
        lesson_id=lesson.id,
        netology_id="item-123",
        title="Test Webinar",
        item_type="webinar",
        video_url="https://kinescope.io/embed/test123",
        has_vtt=True,
    )
    db.add(item)
    await db.commit()

    return {"program": program, "module": module, "lesson": lesson, "item": item}


@pytest.fixture
async def seed_conspect(db: AsyncSession, seed_program):
    """Создать тестовый конспект."""
    import uuid_utils as uuid

    item = seed_program["item"]
    module = seed_program["module"]
    program = seed_program["program"]

    conspect = Conspect(
        id=uuid.uuid7(),
        user_id=uuid.UUID(TEST_USER_ID),
        lesson_item_id=item.id,
        program_id=program.id,
        module_id=module.id,
        title="Test Conspect",
        topic="Test Topic",
        summary="# Test Summary",
        key_points=["Point 1", "Point 2"],
        definitions=[{"term": "Term", "definition": "Definition"}],
        difficulty=5,
        is_edited=False,
    )
    db.add(conspect)
    await db.commit()
    await db.refresh(conspect)
    return conspect


# ---------------------------------------------------------------------------
# API Tests
# ---------------------------------------------------------------------------

class TestConspectAPI:
    """Тесты CRUD конспектов."""

    def test_list_conspects_unauthorized(self):
        response = client.get("/api/summary/conspects")
        assert response.status_code == 401

    def test_get_conspect_unauthorized(self):
        response = client.get("/api/summary/conspects/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 401

    def test_update_conspect_unauthorized(self):
        response = client.patch(
            "/api/summary/conspects/123e4567-e89b-12d3-a456-426614174000",
            json={"summary": "Updated"},
        )
        assert response.status_code == 401

    def test_delete_conspect_unauthorized(self):
        response = client.delete(
            "/api/summary/conspects/123e4567-e89b-12d3-a456-426614174000"
        )
        assert response.status_code == 401

    def test_recent_conspects_unauthorized(self):
        response = client.get("/api/summary/conspects/recent")
        assert response.status_code == 401

    def test_knowledge_graph_unauthorized(self):
        response = client.get("/api/summary/knowledge-graph")
        assert response.status_code == 401


class TestConspectGenerationFlow:
    """Тесты потока генерации конспекта."""

    @pytest.mark.asyncio
    async def test_create_job_for_nonexistent_item(self, db: AsyncSession):
        response = client.post(
            "/api/summary/conspects/generate",
            json={"lesson_item_id": "123e4567-e89b-12d3-a456-426614174000"},
        )
        assert response.status_code == 401  # No session

    @pytest.mark.asyncio
    async def test_job_status_for_nonexistent_job(self, db: AsyncSession):
        response = client.get(
            "/api/summary/conspects/jobs/123e4567-e89b-12d3-a456-426614174000"
        )
        assert response.status_code == 401


class TestTextCompressionService:
    """Тесты сервиса сжатия текста."""

    def test_compress_short_text(self):
        from backend.services.text_compression_service import TextCompressionService
        text = "Это короткий текст."
        result = TextCompressionService.compress(text)
        assert result == text  # Too short, returns as-is

    def test_compress_long_text(self):
        from backend.services.text_compression_service import TextCompressionService
        text = (
            "Первое предложение о машинном обучении. "
            "Второе предложение о нейронных сетях. "
            "Третье предложение о глубоком обучении. "
            "Четвёртое предложение о данных. "
            "Пятое предложение о моделях. "
            "Шестое предложение о тренировке. "
            "Седьмое предложение о валидации. "
            "Восьмое предложение о тестировании. "
            "Девятое предложение о метриках. "
            "Десятое предложение о результатах. "
            "Одиннадцатое предложение о выводах. "
            "Двенадцатое предложение о будущем. "
        )
        result = TextCompressionService.compress(text, sentences_count=3)
        assert len(result) > 0
        assert len(result) < len(text)


class TestLLMSummaryService:
    """Тесты LLM сервиса."""

    def test_build_prompt(self):
        from backend.services.llm_summary_service import LLMSummaryService
        prompt = LLMSummaryService._build_prompt("Test text", "Test Title")
        assert "Test Title" in prompt
        assert "Test text" in prompt
        assert "topic" in prompt
        assert "summary" in prompt
