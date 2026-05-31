"""Pydantic-схемы для курсов и программ Netology."""

from pydantic import BaseModel


class CourseModule(BaseModel):
    """Модуль внутри профессии/бакалавриата."""

    title: str
    progress: int  # 0-100
    link: str | None = None  # ссылка на модуль в Netology


class CourseResponse(BaseModel):
    """Ответ с данными курса/программы для фронтенда."""

    id: int
    title: str
    type: str  # "Курс" | "Профессия"
    progress: int  # 0-100
    passed: bool
    modules: list[CourseModule] = []
