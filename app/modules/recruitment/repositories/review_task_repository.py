from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.review_task_status import (
    ReviewTaskStatus,
)
from backend.app.models.recruitment.review_task import (
    ReviewTask,
)


class ReviewTaskRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        review_task: ReviewTask,
    ) -> ReviewTask:

        db.add(
            review_task,
        )

        return review_task

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        id: UUID,
    ) -> ReviewTask | None:

        query = await db.execute(
            select(
                ReviewTask,
            ).where(
                ReviewTask.id == id,
            )
        )

        return query.scalar_one_or_none()

    @staticmethod
    async def get_by_job_id(
        db: AsyncSession,
        job_id: UUID,
    ) -> list[ReviewTask]:

        query = await db.execute(
            select(
                ReviewTask,
            )
            .where(
                ReviewTask.job_id == job_id,
            )
            .order_by(
                ReviewTask.created_at.asc(),
            )
        )

        return query.scalars().all()

    @staticmethod
    async def get_queued(
        db: AsyncSession,
    ) -> list[ReviewTask]:

        query = await db.execute(
            select(
                ReviewTask,
            )
            .where(
                ReviewTask.status
                == ReviewTaskStatus.QUEUED,
            )
            .order_by(
                ReviewTask.created_at.asc(),
            )
        )

        return query.scalars().all()