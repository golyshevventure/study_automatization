"""FastAPI роутер для модуля «Календарь v2.0».

Endpoints:
- GET /api/calendar/month  — события за месяц
- GET /api/calendar/week   — события за неделю (ISO)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.dependencies.session_dep import get_current_session
from backend.models.session import UserSession
from backend.schemas.calendar import CalendarMonthResponse, CalendarWeekResponse
from backend.services.calendar_service import CalendarService

router = APIRouter(prefix="/calendar", tags=["calendar"])


VALID_FILTERS = {"all", "lessons", "works", "control"}


def _validate_filter(filter_type: str) -> None:
    if filter_type not in VALID_FILTERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неверный фильтр. Доступны: {', '.join(sorted(VALID_FILTERS))}",
        )


@router.get(
    "/month",
    response_model=CalendarMonthResponse,
    summary="События за месяц",
    description="Возвращает события, сгруппированные по дням месяца.",
)
async def calendar_month(
    year: int = Query(..., ge=2000, le=2100, description="Год"),
    month: int = Query(..., ge=1, le=12, description="Месяц (1-12)"),
    filter_type: str = Query("all", alias="filter", description="all | lessons | works | control"),
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> CalendarMonthResponse:
    _validate_filter(filter_type)

    service = CalendarService(db)
    result = await service.get_month(
        user_id=session.user_id,
        year=year,
        month=month,
        filter_type=filter_type,
    )

    return CalendarMonthResponse(**result)


@router.get(
    "/week",
    response_model=CalendarWeekResponse,
    summary="События за неделю",
    description="Возвращает события, сгруппированные по дням ISO-недели.",
)
async def calendar_week(
    year: int = Query(..., ge=2000, le=2100, description="ISO-год"),
    week: int = Query(..., ge=1, le=53, description="ISO-неделя (1-53)"),
    filter_type: str = Query("all", alias="filter", description="all | lessons | works | control"),
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> CalendarWeekResponse:
    _validate_filter(filter_type)

    service = CalendarService(db)
    result = await service.get_week(
        user_id=session.user_id,
        year=year,
        week=week,
        filter_type=filter_type,
    )

    return CalendarWeekResponse(**result)
