"""Pydantic-схемы для модуля «Генерация конспектов»."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Netology structure (programs / modules / webinars)
# ---------------------------------------------------------------------------

class NetologyProgramResponse(BaseModel):
    """Программа / профессия."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    netology_id: str
    title: str
    program_type: str


class NetologyModuleResponse(BaseModel):
    """Модуль / дисциплина."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    netology_id: str
    title: str
    program_id: UUID


class NetologyLessonItemResponse(BaseModel):
    """Вебинар / видео для выбора."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    netology_id: str
    title: str
    item_type: str
    has_vtt: bool


# ---------------------------------------------------------------------------
# Conspect content (structured LLM output)
# ---------------------------------------------------------------------------

class DefinitionItem(BaseModel):
    """Определение термина."""

    term: str
    definition: str


class ConspectContent(BaseModel):
    """Структурированное содержимое конспекта (генерируется LLM)."""

    topic: str
    summary: str
    key_points: list[str]
    definitions: list[DefinitionItem]
    difficulty: int = Field(ge=1, le=10)


# ---------------------------------------------------------------------------
# Conspect API
# ---------------------------------------------------------------------------

class ConspectCreateRequest(BaseModel):
    """Запрос на генерацию конспекта."""

    lesson_item_id: UUID


class ConspectJobResponse(BaseModel):
    """Статус фоновой задачи."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    error_message: str | None
    retry_count: int
    conspect_id: UUID | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class ConspectResponse(BaseModel):
    """Конспект (список)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    topic: str | None
    program_id: UUID | None
    module_id: UUID | None
    lesson_item_id: UUID
    is_edited: bool
    difficulty: int | None
    created_at: datetime
    updated_at: datetime


class ConspectDetailResponse(BaseModel):
    """Полный конспект с содержимым."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    topic: str | None
    summary: str | None
    key_points: list[str] | None
    definitions: list[dict[str, Any]] | None
    difficulty: int | None
    raw_vtt_length: int | None = Field(default=None)
    is_edited: bool
    created_at: datetime
    updated_at: datetime


class ConspectUpdateRequest(BaseModel):
    """Редактирование конспекта."""

    title: str | None = None
    summary: str | None = None
    key_points: list[str] | None = None
    definitions: list[DefinitionItem] | None = None


class ConspectListResponse(BaseModel):
    """Список конспектов."""

    items: list[ConspectResponse]
    total: int


# ---------------------------------------------------------------------------
# Search / filters
# ---------------------------------------------------------------------------

class ConspectSearchQuery(BaseModel):
    """Параметры поиска."""

    q: str | None = None
    program_id: UUID | None = None
    module_id: UUID | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# ---------------------------------------------------------------------------
# Knowledge Graph
# ---------------------------------------------------------------------------

class GraphNode(BaseModel):
    """Узел графа знаний."""

    id: str
    label: str
    type: str  # program | module | conspect
    color: str | None = None


class GraphEdge(BaseModel):
    """Ребро графа знаний."""

    source: str
    target: str


class KnowledgeGraphResponse(BaseModel):
    """Данные для графа знаний."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
