"""Модели для модуля «Генерация конспектов»."""

import uuid_utils as uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base


def generate_uuid7() -> uuid.UUID:
    """Генерирует UUID v7 — временной + рандомный."""
    return uuid.uuid7()


# ---------------------------------------------------------------------------
# Кэш структуры Netology (read-only mirror)
# ---------------------------------------------------------------------------

class NetologyProgram(Base):
    """Программа / профессия из Netology."""

    __tablename__ = "netology_programs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid7
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_sessions.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    netology_id: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    program_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="program"
    )  # "profession" | "program"
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relations
    modules: Mapped[list["NetologyModule"]] = relationship(
        back_populates="program", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<NetologyProgram {self.title} ({self.netology_id})>"


class NetologyModule(Base):
    """Модуль / дисциплина внутри программы."""

    __tablename__ = "netology_modules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid7
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("netology_programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    netology_id: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # Relations
    program: Mapped["NetologyProgram"] = relationship(back_populates="modules")
    lessons: Mapped[list["NetologyLesson"]] = relationship(
        back_populates="module", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<NetologyModule {self.title}>"


class NetologyLesson(Base):
    """Занятие внутри модуля."""

    __tablename__ = "netology_lessons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid7
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("netology_modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    netology_id: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # Relations
    module: Mapped["NetologyModule"] = relationship(back_populates="lessons")
    items: Mapped[list["NetologyLessonItem"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<NetologyLesson {self.title}>"


class NetologyLessonItem(Base):
    """Item занятия (видео, вебинар, текст, тест и т.д.)."""

    __tablename__ = "netology_lesson_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid7
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("netology_lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    netology_id: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    item_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # video | webinar | text | attachment | test | poll | ...
    video_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    has_vtt: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )
    vtt_extracted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relations
    lesson: Mapped["NetologyLesson"] = relationship(back_populates="items")
    conspects: Mapped[list["Conspect"]] = relationship(
        back_populates="lesson_item", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<NetologyLessonItem {self.title} ({self.item_type})>"


# ---------------------------------------------------------------------------
# Конспекты и задачи
# ---------------------------------------------------------------------------

class Conspect(Base):
    """Сгенерированный конспект."""

    __tablename__ = "conspects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid7
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_sessions.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("netology_lesson_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("netology_programs.id", ondelete="SET NULL"),
        nullable=True,
    )
    module_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("netology_modules.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_points: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    definitions: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    difficulty: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # 1–10

    # Raw sources (optional, for debugging/regeneration)
    raw_vtt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    compressed_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    is_edited: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relations
    lesson_item: Mapped["NetologyLessonItem"] = relationship(
        back_populates="conspects"
    )
    jobs: Mapped[list["ConspectJob"]] = relationship(
        back_populates="conspect", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Conspect {self.title} edited={self.is_edited}>"


class ConspectJob(Base):
    """Фоновая задача на генерацию конспекта."""

    __tablename__ = "conspect_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=generate_uuid7
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_sessions.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("netology_lesson_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conspect_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conspects.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queued",
        index=True,
    )  # queued | extracting | generating | ready | failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relations
    conspect: Mapped[Optional["Conspect"]] = relationship(back_populates="jobs")

    def __repr__(self) -> str:
        return f"<ConspectJob status={self.status} retries={self.retry_count}>"
