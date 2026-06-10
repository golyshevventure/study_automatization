"""Сервис генерации конспектов через LLM (OpenRouter)."""

import asyncio
import json
import logging
from typing import Protocol, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from backend.core.config import settings
from backend.schemas.summary import ConspectContent

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMProvider(Protocol):
    """Протокол провайдера LLM."""

    async def generate(self, prompt: str, schema: type[T]) -> T:
        """Генерирует структурированный ответ по промпту."""


class OpenRouterProvider:
    """Провайдер OpenRouter с structured JSON output."""

    MODEL = "deepseek/deepseek-chat-v3-0324"
    BASE_URL = "https://openrouter.ai/api/v1"
    MAX_RETRIES = 2
    RETRY_DELAY = 1.0

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or getattr(settings, "OPENROUTER_API_KEY", "")
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=httpx.Timeout(60.0, connect=10.0),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://studycore.local",
                "X-Title": "StudyCore",
            },
        )

    async def generate(self, prompt: str, schema: type[T]) -> T:
        """Отправляет запрос к OpenRouter с retry-логикой и валидацией JSON."""
        last_exception: Exception | None = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = await self.client.post(
                    "/chat/completions",
                    json={
                        "model": self.MODEL,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "Ты — ассистент для создания образовательных конспектов. "
                                    "Отвечай строго в формате JSON."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "response_format": {"type": "json_object"},
                    },
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                return schema.model_validate(parsed)
            except (httpx.HTTPError, json.JSONDecodeError, ValidationError, KeyError) as exc:
                last_exception = exc
                logger.warning("OpenRouter attempt %d failed: %s", attempt + 1, exc)
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.RETRY_DELAY)

        raise RuntimeError(
            f"OpenRouter failed after {self.MAX_RETRIES + 1} attempts"
        ) from last_exception

    async def close(self) -> None:
        await self.client.aclose()


class LLMSummaryService:
    """Высокоуровневый сервис генерации конспекта."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or OpenRouterProvider()

    async def generate_conspect(
        self, compressed_text: str, title: str
    ) -> ConspectContent:
        """Генерирует структурированный конспект из сжатого текста."""
        prompt = self._build_prompt(compressed_text, title)
        return await self.provider.generate(prompt, ConspectContent)

    @staticmethod
    def _build_prompt(compressed_text: str, title: str) -> str:
        return (
            f"На основе следующей лекции «{title}» создай образовательный "
            "конспект на русском языке.\n\n"
            "Верни строго JSON с полями:\n"
            "- topic: краткая тема лекции (1 предложение)\n"
            "- summary: развернутое изложение основного содержания (3–5 абзацев)\n"
            "- key_points: список ключевых тезисов (5–10 строк)\n"
            "- definitions: список объектов с полями term и definition "
            "(важные термины и их определения)\n"
            "- difficulty: оценка сложности материала от 1 до 10\n\n"
            f"Текст лекции:\n{compressed_text}\n"
        )
