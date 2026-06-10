"""Настройки StudyCore backend.

Загружает переменные из .env и предоставляет typed-конфиг.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Загружаем .env из корня проекта (родитель backend/)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


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

    # OpenRouter
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")


settings = Settings()
