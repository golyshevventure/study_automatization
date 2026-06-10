"""ARQ-воркер для фоновой генерации конспектов.

Запуск:
    arq backend.workers.summary_worker.WorkerSettings
"""

import logging
import os
import sys
from datetime import datetime, timezone
from uuid import UUID

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import settings
from backend.models.summary import Conspect, ConspectJob, NetologyLessonItem
from backend.schemas.summary import ConspectContent
from backend.services.conspect_job_service import ConspectJobService
from backend.services.llm_summary_service import LLMSummaryService
from backend.services.text_compression_service import TextCompressionService
from backend.services.vtt_extraction_service import VTTExtractionService

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/tmp/summary_worker.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("summary_worker")

# Engine для воркера (отдельный от FastAPI)
_worker_engine = None


def _get_engine():
    global _worker_engine
    if _worker_engine is None:
        _worker_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            future=True,
        )
    return _worker_engine


async def _get_session() -> AsyncSession:
    engine = _get_engine()
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    return session_maker()


async def generate_conspect_task(ctx, job_id: str, user_id: str, lesson_item_id: str):
    """Фоновая задача: извлечь VTT → сжать → сгенерировать конспект через LLM."""
    job_uuid = UUID(job_id)
    user_uuid = UUID(user_id)
    item_uuid = UUID(lesson_item_id)

    db = await _get_session()
    llm_service = LLMSummaryService()

    try:
        # 1. Status = extracting
        await ConspectJobService.update_status(job_uuid, "extracting", db)
        logger.info("Задача %s: извлечение VTT", job_id)

        # 2. Fetch lesson item
        item = await db.get(NetologyLessonItem, item_uuid)
        if not item or not item.video_url:
            raise ValueError("Вебинар не найден или не имеет video_url")

        # 3. Extract VTT
        raw_vtt = await VTTExtractionService.extract_vtt(item.video_url)
        if not raw_vtt:
            raise ValueError("Субтитры (VTT) не найдены для этого вебинара")

        # Update item cache
        item.has_vtt = True
        item.vtt_extracted_at = datetime.now(timezone.utc)
        await db.commit()

        # 4. Compress text
        compressed = TextCompressionService.compress(raw_vtt)
        logger.info(
            "Задача %s: VTT %d символов → сжато %d символов",
            job_id,
            len(raw_vtt),
            len(compressed),
        )

        # 5. Status = generating
        await ConspectJobService.update_status(job_uuid, "generating", db)
        logger.info("Задача %s: вызов LLM", job_id)

        # 6. LLM generation
        content: ConspectContent = await llm_service.generate_conspect(
            compressed, item.title
        )
        logger.info("Задача %s: LLM готово, тема=%s", job_id, content.topic)

        # 7. Build program_id / module_id from item relations
        program_id = None
        module_id = None
        if item.lesson and item.lesson.module:
            module_id = item.lesson.module.id
            if item.lesson.module.program:
                program_id = item.lesson.module.program.id

        # 8. Save conspect
        conspect = Conspect(
            user_id=user_uuid,
            lesson_item_id=item_uuid,
            program_id=program_id,
            module_id=module_id,
            title=item.title,
            topic=content.topic,
            summary=content.summary,
            key_points=content.key_points,
            definitions=[d.model_dump() for d in content.definitions],
            difficulty=content.difficulty,
            raw_vtt=raw_vtt,
            compressed_text=compressed,
            is_edited=False,
        )
        db.add(conspect)
        await db.commit()
        await db.refresh(conspect)

        # 9. Status = ready
        await ConspectJobService.update_status(
            job_uuid, "ready", db, conspect_id=conspect.id
        )
        logger.info("Задача %s: завершена, conspect_id=%s", job_id, conspect.id)

    except Exception as exc:
        logger.exception("Задача %s провалена", job_id)
        error_msg = str(exc)[:500]
        await ConspectJobService.update_status(
            job_uuid, "failed", db, error_message=error_msg
        )
        raise  # ARQ будет retry

    finally:
        await llm_service.close()
        await db.close()


class WorkerSettings:
    """Конфигурация ARQ-воркера."""

    redis_settings = RedisSettings(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
    )
    functions = [generate_conspect_task]
    max_jobs = 5
    job_timeout = 300  # 5 минут
    max_tries = 3
    retry_delay = 10  # секунд перед первым retry
