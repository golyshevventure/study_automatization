"""FastAPI роутер для модуля «Ближайшие события и дедлайны».

Endpoints:
- POST /api/deadlines/sync — синхронизация с Netology
- GET  /api/deadlines — список будущих событий
- GET  /api/deadlines/{event_id} — детали события
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.dependencies.session_dep import get_current_session
from backend.models.session import UserSession
from backend.schemas.deadline import (
    DeadlineEventDetailResponse,
    DeadlineEventResponse,
    DeadlineListResponse,
    DeadlineSyncResponse,
)
from backend.services.deadline_service import DeadlineService

# ---------------------------------------------------------------------------
# Роутер
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/deadlines", tags=["deadlines"])


# ---------------------------------------------------------------------------
# Pydantic-схемы запросов
# ---------------------------------------------------------------------------


class SyncResponse(DeadlineSyncResponse):
    """Ответ на синхронизацию."""

    pass


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/sync",
    response_model=SyncResponse,
    summary="Синхронизировать дедлайны",
    description=(
        "Запрашивает актуальные данные из Netology API, "
        "объединяет, группирует и сохраняет в БД."
    ),
)
async def sync_deadlines(
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> SyncResponse:
    """Синхронизировать дедлайны с Netology API."""
    if not session.cookies_json:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cookies не найдены. Авторизуйтесь заново.",
        )

    service = DeadlineService(db)
    result = await service.sync(
        user_id=session.user_id,
        cookies=session.cookies_json,
    )

    return SyncResponse(**result)


@router.get(
    "",
    response_model=DeadlineListResponse,
    summary="Список ближайших событий",
    description=(
        "Возвращает будущие события (дедлайны, зачёты, экзамены, занятия). "
        "Поддерживает фильтрацию по категориям."
    ),
)
async def list_deadlines(
    filter_type: str = Query("all", alias="filter", description="all | lessons | works | control"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    program: str | None = Query(None, description="Фильтр по названию программы"),
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> DeadlineListResponse:
    """Получить список будущих событий."""
    # Валидация фильтра
    valid_filters = {"all", "lessons", "works", "control"}
    if filter_type not in valid_filters:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неверный фильтр. Доступны: {', '.join(valid_filters)}",
        )

    service = DeadlineService(db)
    events, total = await service.list_events(
        user_id=session.user_id,
        filter_type=filter_type,
        limit=limit,
        offset=offset,
        program=program,
    )

    return DeadlineListResponse(
        events=[DeadlineEventResponse.model_validate(e) for e in events],
        total=total,
        filter=filter_type,
    )


@router.get(
    "/{event_id}",
    response_model=DeadlineEventDetailResponse,
    summary="Детали события",
    description="Возвращает одно событие с детализацией raw_items.",
)
async def get_deadline(
    event_id: str,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> DeadlineEventDetailResponse:
    """Получить детали одного события."""
    service = DeadlineService(db)
    event = await service.get_event(session.user_id, event_id)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Событие не найдено",
        )

    return DeadlineEventDetailResponse.model_validate(event)
