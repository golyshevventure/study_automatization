"""FastAPI роутер для получения активных программ Netology.

Endpoints:
- GET /api/programs — список активных курсов с прогрессом
- GET /api/programs/{program_id} — один курс по ID
"""

import time
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import AsyncSessionLocal
from backend.dependencies.session_dep import get_current_session
from backend.models.session import UserSession
from backend.schemas.course import CourseResponse
from backend.services.netology_programs_service import NetologyProgramsService

router = APIRouter(tags=["programs"])

# In-memory rate limiter: {user_id: last_request_timestamp}
_netology_rate_limit: dict[str, float] = {}
RATE_LIMIT_SECONDS = 15.0  # не чаще 1 запроса к Netology в 15 сек
CACHE_TTL_SECONDS = 300    # кэш свежий 5 минут


def _is_rate_limited(user_id: str) -> bool:
    """Проверить, не превышен ли rate limit для пользователя."""
    now = time.time()
    last = _netology_rate_limit.get(user_id)
    if last is not None and (now - last) < RATE_LIMIT_SECONDS:
        return True
    _netology_rate_limit[user_id] = now
    return False


def _cache_is_fresh(cached_at: datetime | None) -> bool:
    """Проверить, не устарел ли кэш."""
    if cached_at is None:
        return False
    return datetime.now(timezone.utc) - cached_at < timedelta(seconds=CACHE_TTL_SECONDS)


async def _get_programs_with_cache(
    session: UserSession,
) -> list[dict]:
    """Получить программы с кэшированием и rate limiting.

    Логика:
    1. Если кэш свежий (< 5 мин) — возвращаем кэш
    2. Если кэш устарел и rate limit OK — идём в Netology, обновляем кэш
    3. Если кэш устарел и rate limit сработал — возвращаем устаревший кэш (graceful degradation)
    4. Если кэша нет и rate limit сработал — возвращаем 429
    """
    user_id_str = str(session.user_id)

    # 1. Кэш свежий — отдаём сразу
    if _cache_is_fresh(session.programs_cached_at) and session.programs_cache_json:
        return session.programs_cache_json

    # 2. Кэш устарел или отсутствует
    if _is_rate_limited(user_id_str):
        # Rate limit сработал — отдаём устаревший кэш, если есть
        if session.programs_cache_json:
            return session.programs_cache_json
        raise HTTPException(
            status_code=429,
            detail="Слишком много запросов. Попробуйте через несколько секунд.",
        )

    # 3. Идём в Netology
    try:
        service = NetologyProgramsService()
        courses = service.get_active_courses(session.cookies_json)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Сессия Netology истекла",
            )
        # Если Netology недоступна — отдаём кэш, если есть
        if session.programs_cache_json:
            return session.programs_cache_json
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка Netology API: {exc.response.status_code}",
        )
    except Exception as exc:
        if session.programs_cache_json:
            return session.programs_cache_json
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка: {exc}",
        )

    # 4. Сохраняем в кэш (в отдельной сессии БД)
    async with AsyncSessionLocal() as db:
        merged = await db.merge(session)
        merged.programs_cache_json = courses
        merged.programs_cached_at = datetime.now(timezone.utc)
        await db.commit()
    return courses


@router.get("/programs", response_model=list[CourseResponse])
async def get_programs(
    session: UserSession = Depends(get_current_session),
):
    """Вернуть активные программы пользователя с прогрессом.

    Данные кэшируются на 5 минут. Rate limit: 1 запрос к Netology в 15 сек.
    """
    courses = await _get_programs_with_cache(session)
    return courses


@router.get("/programs/{program_id}", response_model=CourseResponse)
async def get_program(
    program_id: int,
    session: UserSession = Depends(get_current_session),
):
    """Вернуть одну активную программу по ID с прогрессом.

    Использует тот же кэш, что и /programs (не делает лишних запросов к Netology).
    """
    courses = await _get_programs_with_cache(session)
    for course in courses:
        if course["id"] == program_id:
            return course
    raise HTTPException(status_code=404, detail="Курс не найден")
