"""Настройки StudyCore backend.

Загружает переменные из .env и предоставляет typed-конфиг.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Конфигурация приложения."""

    # PostgreSQL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://studycore_user:studycore_pass@localhost:5432/studycore",
    )

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-jwt-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # Netology
    NETOLOGY_EMAIL: str = os.getenv("NETOLOGY_EMAIL", "")
    NETOLOGY_PASSWORD: str = os.getenv("NETOLOGY_PASSWORD", "")


settings = Settings()
