"""Сервис управления фоновыми задачами на генерацию конспектов."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.summary import ConspectJob


class ConspectJobService:
    """CRUD-операции для ConspectJob."""

    @staticmethod
    async def create_job(
        user_id: UUID,
        lesson_item_id: UUID,
        db: AsyncSession,
    ) -> ConspectJob:
        """Создаёт новую задачу в статусе queued."""
        job = ConspectJob(
            user_id=user_id,
            lesson_item_id=lesson_item_id,
            status="queued",
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def update_status(
        job_id: UUID,
        status: str,
        db: AsyncSession,
        *,
        conspect_id: UUID | None = None,
        error_message: str | None = None,
        retry_count: int | None = None,
    ) -> ConspectJob | None:
        """Обновляет статус задачи и связанные поля."""
        job = await db.get(ConspectJob, job_id)
        if not job:
            return None

        job.status = status
        if conspect_id is not None:
            job.conspect_id = conspect_id
        if error_message is not None:
            job.error_message = error_message
        if retry_count is not None:
            job.retry_count = retry_count

        now = datetime.now(timezone.utc)
        if status in ("ready", "failed"):
            job.completed_at = now
        if status == "extracting" and job.started_at is None:
            job.started_at = now

        await db.commit()
        await db.refresh(job)
        return job
