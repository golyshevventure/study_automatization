"""ARQ worker для генерации конспектов.

Запуск:
    python -m backend.workers.summary_worker
"""

import logging
from uuid import UUID

from arq.connections import RedisSettings
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.core.database import AsyncSessionLocal
from backend.models.summary import Conspect, ConspectJob, NetologyLesson, NetologyLessonItem, NetologyModule
from backend.schemas.summary import ConspectContent
from backend.services.conspect_job_service import ConspectJobService
from backend.services.llm_summary_service import LLMSummaryService
from backend.services.text_compression_service import TextCompressionService
from backend.services.vtt_extraction_service import VTTExtractionService

logger = logging.getLogger(__name__)


async def generate_conspect_task(
    ctx: dict,
    job_id: str,
    user_id: str,
    lesson_item_id: str,
) -> None:
    """
    Фоновая задача генерации конспекта.

    Flow: extracting → compressing → generating → ready
    """
    job_uuid = UUID(job_id)
    user_uuid = UUID(user_id)
    lesson_item_uuid = UUID(lesson_item_id)

    db = AsyncSessionLocal()
    job_service = ConspectJobService()

    try:
        # --- extracting -----------------------------------------------------
        await job_service.update_status(job_uuid, "extracting", db)

        stmt = (
            select(NetologyLessonItem)
            .where(NetologyLessonItem.id == lesson_item_uuid)
            .options(
                selectinload(NetologyLessonItem.lesson).selectinload(
                    NetologyLesson.module
                ).selectinload(NetologyModule.program)
            )
        )
        result = await db.execute(stmt)
        item = result.scalar_one_or_none()
        if not item or not item.video_url:
            raise ValueError("Вебинар не найден или отсутствует video_url")

        vtt_text = await VTTExtractionService.extract_vtt(item.video_url)
        if not vtt_text:
            raise ValueError("Не удалось извлечь VTT-субтитры")

        # --- compressing ----------------------------------------------------
        await job_service.update_status(job_uuid, "compressing", db)

        compressed = TextCompressionService.compress(vtt_text, sentences_count=10)

        # --- generating -----------------------------------------------------
        await job_service.update_status(job_uuid, "generating", db)

        llm_service = LLMSummaryService()
        try:
            content: ConspectContent = await llm_service.generate_conspect(
                compressed, item.title
            )
        finally:
            await llm_service.provider.close()

        # --- save conspect --------------------------------------------------
        program_id = None
        module_id = None
        if item.lesson and item.lesson.module:
            module_id = item.lesson.module.id
            if item.lesson.module.program:
                program_id = item.lesson.module.program.id

        conspect = Conspect(
            user_id=user_uuid,
            lesson_item_id=lesson_item_uuid,
            program_id=program_id,
            module_id=module_id,
            title=item.title,
            topic=content.topic,
            summary=content.summary,
            key_points=content.key_points,
            definitions=[d.model_dump() for d in content.definitions],
            difficulty=content.difficulty,
            raw_vtt=vtt_text,
            compressed_text=compressed,
        )
        db.add(conspect)
        await db.commit()
        await db.refresh(conspect)

        # --- ready ----------------------------------------------------------
        await job_service.update_status(
            job_uuid, "ready", db, conspect_id=conspect.id
        )

        logger.info("Conspect generated: %s for job %s", conspect.id, job_id)

    except Exception as exc:
        logger.exception("Conspect generation failed for job %s", job_id)
        try:
            await job_service.update_status(
                job_uuid,
                "failed",
                db,
                error_message=str(exc)[:500],
            )
        except Exception:
            logger.exception("Failed to update job status to failed")
    finally:
        await db.close()


class WorkerSettings:
    """Настройки ARQ worker для генерации конспектов."""

    functions = [generate_conspect_task]
    redis_settings = RedisSettings(
        host="localhost",
        port=6379,
        database=0,
    )
    max_jobs = 5
    job_timeout = 300
    keep_result = 3600


if __name__ == "__main__":
    import asyncio

    from arq.worker import run_worker

    asyncio.run(run_worker(WorkerSettings))
