"""FastAPI роутер для модуля «Генерация конспектов».

Endpoints:
- GET  /api/summary/programs          — список программ
- GET  /api/summary/programs/{id}/modules  — модули программы
- GET  /api/summary/modules/{id}/webinars  — вебинары модуля (только с VTT)
- POST /api/summary/conspects/generate     — запустить генерацию
- GET  /api/summary/conspects/jobs/{id}    — статус задачи
- GET  /api/summary/conspects              — список конспектов
- GET  /api/summary/conspects/{id}         — детали конспекта
- PATCH /api/summary/conspects/{id}        — редактировать конспект
- DELETE /api/summary/conspects/{id}       — удалить конспект
- GET  /api/summary/conspects/recent       — 3 последних конспекта
- GET  /api/summary/knowledge-graph        — граф знаний
"""

from uuid import UUID

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import array_agg
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import get_db
from backend.dependencies.session_dep import get_current_session
from backend.models.session import UserSession
from backend.models.summary import Conspect, ConspectJob, NetologyLessonItem
from backend.schemas.summary import (
    ConspectCreateRequest,
    ConspectDetailResponse,
    ConspectJobResponse,
    ConspectListResponse,
    ConspectResponse,
    ConspectSearchQuery,
    ConspectUpdateRequest,
    KnowledgeGraphResponse,
    NetologyLessonItemResponse,
    NetologyModuleResponse,
    NetologyProgramResponse,
)
from backend.services.conspect_job_service import ConspectJobService
from backend.services.netology_program_service import NetologyProgramService
from backend.services.vtt_extraction_service import VTTExtractionService

router = APIRouter(prefix="/summary", tags=["summary"])


# ---------------------------------------------------------------------------
# Programs / Modules / Webinars
# ---------------------------------------------------------------------------

@router.get(
    "/programs",
    response_model=list[NetologyProgramResponse],
    summary="Список программ",
)
async def list_programs(
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> list[NetologyProgramResponse]:
    service = NetologyProgramService(db)
    try:
        programs = await service.get_user_programs()
        return programs
    finally:
        await service.close()


@router.get(
    "/programs/{program_id}/modules",
    response_model=list[NetologyModuleResponse],
    summary="Модули программы",
)
async def list_modules(
    program_id: UUID,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> list[NetologyModuleResponse]:
    service = NetologyProgramService(db)
    try:
        modules = await service.get_program_modules(program_id)
        return modules
    finally:
        await service.close()


@router.get(
    "/modules/{module_id}/webinars",
    response_model=list[NetologyLessonItemResponse],
    summary="Вебинары модуля (только с VTT)",
)
async def list_webinars(
    module_id: UUID,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> list[NetologyLessonItemResponse]:
    service = NetologyProgramService(db)
    try:
        items = await service.get_module_webinars(module_id, only_with_vtt=True)
        return items
    finally:
        await service.close()


# ---------------------------------------------------------------------------
# Conspect Generation
# ---------------------------------------------------------------------------

@router.post(
    "/conspects/generate",
    response_model=ConspectJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Создать конспект",
)
async def generate_conspect(
    request: ConspectCreateRequest,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> ConspectJobResponse:
    # Validate lesson_item exists and has VTT
    item = await db.get(NetologyLessonItem, request.lesson_item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вебинар не найден",
        )

    # Quick VTT check
    if item.video_url and not item.has_vtt:
        vtt_text = await VTTExtractionService.extract_vtt(item.video_url)
        if vtt_text:
            item.has_vtt = True
            await db.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="У этого вебинара нет субтитров (VTT)",
            )

    # Create job
    job_service = ConspectJobService()
    job = await job_service.create_job(
        user_id=session.user_id,
        lesson_item_id=request.lesson_item_id,
        db=db,
    )

    # Enqueue ARQ background task
    redis_pool = await create_pool(
        RedisSettings.from_dsn(settings.REDIS_URL)
    )
    await redis_pool.enqueue_job(
        "generate_conspect_task",
        str(job.id),
        str(session.user_id),
        str(request.lesson_item_id),
    )
    await redis_pool.close()

    return job


@router.get(
    "/conspects/jobs/{job_id}",
    response_model=ConspectJobResponse,
    summary="Статус генерации",
)
async def get_job_status(
    job_id: UUID,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> ConspectJobResponse:
    job = await db.get(ConspectJob, job_id)
    if not job or job.user_id != session.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Задача не найдена",
        )
    return job


# ---------------------------------------------------------------------------
# Conspect CRUD + Search
# ---------------------------------------------------------------------------

@router.get(
    "/conspects",
    response_model=ConspectListResponse,
    summary="Список конспектов",
)
async def list_conspects(
    q: str | None = Query(None, description="Поиск по названию и содержанию"),
    program_id: UUID | None = Query(None),
    module_id: UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> ConspectListResponse:
    query = select(Conspect).where(Conspect.user_id == session.user_id)

    if program_id:
        query = query.where(Conspect.program_id == program_id)
    if module_id:
        query = query.where(Conspect.module_id == module_id)
    if q:
        # PostgreSQL full-text search (Russian)
        query = query.where(
            func.to_tsvector("russian", func.coalesce(Conspect.title, "") + " " + func.coalesce(Conspect.summary, "")).op("@@")(
                func.plainto_tsquery("russian", q)
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Fetch page
    query = query.order_by(Conspect.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return ConspectListResponse(
        items=items,
        total=total,
    )


@router.get(
    "/conspects/{conspect_id}",
    response_model=ConspectDetailResponse,
    summary="Детали конспекта",
)
async def get_conspect(
    conspect_id: UUID,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> ConspectDetailResponse:
    conspect = await db.get(Conspect, conspect_id)
    if not conspect or conspect.user_id != session.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Конспект не найден",
        )

    # Build response with raw_vtt_length
    response_data = {
        **conspect.__dict__,
        "raw_vtt_length": len(conspect.raw_vtt) if conspect.raw_vtt else None,
    }
    return ConspectDetailResponse.model_validate(response_data)


@router.patch(
    "/conspects/{conspect_id}",
    response_model=ConspectDetailResponse,
    summary="Редактировать конспект",
)
async def update_conspect(
    conspect_id: UUID,
    request: ConspectUpdateRequest,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> ConspectDetailResponse:
    conspect = await db.get(Conspect, conspect_id)
    if not conspect or conspect.user_id != session.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Конспект не найден",
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(conspect, field, value)

    conspect.is_edited = True
    await db.commit()
    await db.refresh(conspect)

    response_data = {
        **conspect.__dict__,
        "raw_vtt_length": len(conspect.raw_vtt) if conspect.raw_vtt else None,
    }
    return ConspectDetailResponse.model_validate(response_data)


@router.delete(
    "/conspects/{conspect_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить конспект",
)
async def delete_conspect(
    conspect_id: UUID,
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> None:
    conspect = await db.get(Conspect, conspect_id)
    if not conspect or conspect.user_id != session.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Конспект не найден",
        )
    await db.delete(conspect)
    await db.commit()


@router.get(
    "/conspects/recent",
    response_model=list[ConspectResponse],
    summary="3 последних конспекта",
)
async def recent_conspects(
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> list[ConspectResponse]:
    result = await db.execute(
        select(Conspect)
        .where(Conspect.user_id == session.user_id)
        .order_by(Conspect.created_at.desc())
        .limit(3)
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Knowledge Graph (placeholder for Phase 4)
# ---------------------------------------------------------------------------

@router.get(
    "/knowledge-graph",
    response_model=KnowledgeGraphResponse,
    summary="Граф знаний",
)
async def knowledge_graph(
    session: UserSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeGraphResponse:
    # TODO: implement in Phase 4
    return KnowledgeGraphResponse(nodes=[], edges=[])
