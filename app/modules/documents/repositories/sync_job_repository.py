# app/repositories/sync_job_repository.py

from sqlalchemy import (
    select
)

from backend.app.modules.documents.models.sync_jobs import (
    SyncJob
    
)

class SyncJobRepository:

    @staticmethod
    async def create(
        db,
        job: SyncJob
    ):

        db.add(job)

        await db.commit()

        await db.refresh(job)

        return job

    @staticmethod
    async def get_latest(
        db
    ):

        result = await db.execute(

            select(
                SyncJob
            )
            .order_by(
                SyncJob.created_at.desc()
            )
            .limit(1)

        )

        return result.scalar_one_or_none()