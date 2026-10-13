# app/services/sync/sync_job_service.py

from uuid import uuid4

from datetime import (
    datetime,
    timezone
)

from backend.app.modules.documents.models.sync_jobs import (
    SyncJob
)

from backend.app.modules.documents.repositories.sync_job_repository import (
    SyncJobRepository
)


class SyncJobService:

    @staticmethod
    async def create_running_job(
        db
    ):

        job = SyncJob(

            id=str(
                uuid4()
            ),

            status="RUNNING",

            created_at=datetime.now(
                timezone.utc
            )

        )

        return await (
            SyncJobRepository
            .create(
                db,
                job
            )
        )

    @staticmethod
    async def complete_latest_job(
        db
    ):

        job = await (
            SyncJobRepository
            .get_latest(
                db
            )
        )

        if not job:
            return

        job.status = "COMPLETED"

        job.completed_at = (
            datetime.now(
                timezone.utc
            )
        )

        await db.commit()

        return job