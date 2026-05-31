"""FastAPI роутер для получения активных программ Netology.

Endpoint:
- GET /api/programs — список активных курсов с прогрессом
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies.session_dep import get_current_session
from backend.models.session import UserSession
from backend.schemas.course import CourseResponse
from backend.services.netology_programs_service import NetologyProgramsService

router = APIRouter(tags=["programs"])


@router.get("/programs", response_model=list[CourseResponse])
async def get_programs(session: UserSession = Depends(get_current_session)):
    """Вернуть активные программы пользователя с прогрессом.

    Данные получаются с Netology API через cookies пользователя.
    Используется комбинация:
    - /programs/calendar/filters (достоверный список активных)
    - /programs/progress (прогресс по модулям)
    """
    try:
        service = NetologyProgramsService()
        return service.get_active_courses(session.cookies_json)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Сессия Netology истекла",
            )
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка Netology API: {exc.response.status_code}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка: {exc}",
        )


@router.get("/programs/{program_id}", response_model=CourseResponse)
async def get_program(
    program_id: int,
    session: UserSession = Depends(get_current_session),
):
    """Вернуть одну активную программу по ID с прогрессом."""
    try:
        service = NetologyProgramsService()
        courses = service.get_active_courses(session.cookies_json)
        for course in courses:
            if course["id"] == program_id:
                return course
        raise HTTPException(status_code=404, detail="Курс не найден")
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Сессия Netology истекла",
            )
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка Netology API: {exc.response.status_code}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Внутренняя ошибка: {exc}",
        )
