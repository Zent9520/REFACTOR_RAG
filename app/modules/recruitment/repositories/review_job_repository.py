from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.recruitment.review_job import ReviewJob


class ReviewJobRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        review_job: ReviewJob,
    ) -> ReviewJob:

        db.add(
            review_job,
        )

        return review_job

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        id: UUID,
    ) -> ReviewJob | None:

        query = await db.execute(
            select(
                ReviewJob,
            ).where(
                ReviewJob.id == id,
            )
        )

        return query.scalar_one_or_none()