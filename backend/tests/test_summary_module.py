"""Тесты для модуля «Генерация конспектов» (Phase 1)."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.main import app
from backend.models.session import UserSession
from backend.models.summary import (
    NetologyLesson,
    NetologyLessonItem,
    NetologyModule,
    NetologyProgram,
)
from backend.services.vtt_extraction_service import VTTExtractionService

client = TestClient(app)
TEST_USER_ID = uuid.UUID("019e788c-8dd1-7e02-8752-9812841d98bd")


async def _create_test_user(db: AsyncSession) -> None:
    """Создать тестового пользователя для FK-constraint."""
    user = UserSession(
        user_id=TEST_USER_ID,
        email="test@example.com",
        netology_session="test-session",
        cookies_json={},
    )
    db.add(user)
    await db.commit()


# ---------------------------------------------------------------------------
# VTT Extraction
# ---------------------------------------------------------------------------

class TestVTTExtraction:
    """Тесты извлечения VTT из Kinescope HTML."""

    def test_parse_vtt_basic(self):
        vtt = """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello world

00:00:05.000 --> 00:00:10.000
This is a test
"""
        result = VTTExtractionService._parse_vtt(vtt)
        assert "Hello world" in result
        assert "This is a test" in result
        assert "00:00:00" not in result
        assert "WEBVTT" not in result

    def test_parse_vtt_empty(self):
        assert VTTExtractionService._parse_vtt("") == ""
        assert VTTExtractionService._parse_vtt("WEBVTT\n\n") == ""

    def test_parse_vtt_with_numbers_and_notes(self):
        vtt = """WEBVTT

1
00:00:01.000 --> 00:00:02.000
First line

NOTE comment
2
00:00:02.000 --> 00:00:03.000
Second line
"""
        result = VTTExtractionService._parse_vtt(vtt)
        assert "First line" in result
        assert "Second line" in result
        assert "NOTE" not in result
        assert "1" not in result  # standalone numbers removed

    @pytest.mark.asyncio
    async def test_extract_vtt_invalid_url(self):
        # Should return empty string for bad URL
        result = await VTTExtractionService.extract_vtt("https://invalid-url-12345.example.com")
        assert result == ""


# ---------------------------------------------------------------------------
# Database Models
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestSummaryModels:
    """Тесты SQLAlchemy моделей."""

    async def test_create_program(self, db: AsyncSession):
        await _create_test_user(db)
        program = NetologyProgram(
            user_id=TEST_USER_ID,
            netology_id="test-prog-123",
            title="Test Program",
            program_type="program",
        )
        db.add(program)
        await db.commit()
        await db.refresh(program)

        assert program.id is not None
        assert program.title == "Test Program"

    async def test_create_module(self, db: AsyncSession):
        await _create_test_user(db)
        program = NetologyProgram(
            user_id=TEST_USER_ID,
            netology_id="test-prog-456",
            title="Test Program 2",
            program_type="profession",
        )
        db.add(program)
        await db.commit()
        await db.refresh(program)

        module = NetologyModule(
            program_id=program.id,
            netology_id="test-mod-123",
            title="Test Module",
        )
        db.add(module)
        await db.commit()
        await db.refresh(module)

        assert module.program_id == program.id
        assert module.title == "Test Module"

    async def test_create_lesson_item(self, db: AsyncSession):
        await _create_test_user(db)
        program = NetologyProgram(
            user_id=TEST_USER_ID,
            netology_id="test-prog-789",
            title="Test Program 3",
            program_type="program",
        )
        db.add(program)
        await db.commit()
        await db.refresh(program)

        module = NetologyModule(
            program_id=program.id,
            netology_id="test-mod-789",
            title="Test Module 2",
        )
        db.add(module)
        await db.commit()
        await db.refresh(module)

        lesson = NetologyLesson(
            module_id=module.id,
            netology_id="test-lesson-789",
            title="Test Lesson",
        )
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)

        item = NetologyLessonItem(
            lesson_id=lesson.id,
            netology_id="test-item-789",
            title="Test Webinar",
            item_type="webinar",
            video_url="https://kinescope.io/test123",
            has_vtt=False,
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)

        assert item.lesson_id == lesson.id
        assert item.item_type == "webinar"
        assert not item.has_vtt


# ---------------------------------------------------------------------------
# API Endpoints (unauthorized)
# ---------------------------------------------------------------------------

class TestSummaryAPIUnauthorized:
    """Тесты API без авторизации."""

    def test_list_programs_unauthorized(self):
        response = client.get("/api/summary/programs")
        assert response.status_code == 401

    def test_list_modules_unauthorized(self):
        response = client.get("/api/summary/programs/123e4567-e89b-12d3-a456-426614174000/modules")
        assert response.status_code == 401

    def test_list_webinars_unauthorized(self):
        response = client.get("/api/summary/modules/123e4567-e89b-12d3-a456-426614174000/webinars")
        assert response.status_code == 401

    def test_generate_conspect_unauthorized(self):
        response = client.post(
            "/api/summary/conspects/generate",
            json={"lesson_item_id": "123e4567-e89b-12d3-a456-426614174000"},
        )
        assert response.status_code == 401
