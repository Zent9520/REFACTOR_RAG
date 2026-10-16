import asyncio
from datetime import datetime, timezone

from backend.app.core.database import AsyncSessionLocal
from backend.app.modules.company.recruitment.enums.review_job_status import ReviewJobStatus
from backend.app.modules.company.recruitment.enums.review_queue import ReviewQueue
from backend.app.modules.company.recruitment.enums.review_task_status import ReviewTaskStatus
from backend.app.modules.company.recruitment.repositories.review_job_repository import ReviewJobRepository
from backend.app.modules.company.recruitment.repositories.review_task_repository import ReviewTaskRepository
from backend.app.modules.company.recruitment.services.review_ai_service import ReviewAIService
from backend.app.shared.queue.local_queue_provider import queue_provider
from backend.app.modules.company.recruitment.reviews.review_task_message import ReviewTaskMessage


async def process_review_task(message: ReviewTaskMessage) -> None:
    async with AsyncSessionLocal() as db:

        review_task = await ReviewTaskRepository.get_by_id(
            db=db,
            id=message.task_id,
        )

        if review_task is None:
            return

        review_job = await ReviewJobRepository.get_by_id(
            db=db,
            id=review_task.job_id,
        )

        if review_job is None:
            return

        try:
            if review_job.started_at is None:
                review_job.started_at = datetime.now(timezone.utc)

            review_job.status = ReviewJobStatus.PROCESSING

            review_task.status = ReviewTaskStatus.PROCESSING
            review_task.started_at = datetime.now(timezone.utc)

            await db.commit()

            ai_result = await ReviewAIService.execute(
                db=db,
                model_id=review_job.model_id,
                job_description=review_job.job_description,
                file_path=review_task.file_path,
            )

            review_task.review_result = ai_result.review_result
            review_task.status = ReviewTaskStatus.COMPLETED
            review_task.completed_at = datetime.now(timezone.utc)

            await db.commit()

        except Exception as ex:
            review_task.status = ReviewTaskStatus.FAILED
            review_task.error_message = str(ex)
            review_task.completed_at = datetime.now(timezone.utc)

            await db.commit()

        tasks = await ReviewTaskRepository.get_by_job_id(
            db=db,
            job_id=review_job.id,
        )

        if all(t.status == ReviewTaskStatus.COMPLETED for t in tasks):
            review_job.status = ReviewJobStatus.COMPLETED
            review_job.completed_at = datetime.now(timezone.utc)

        elif any(t.status == ReviewTaskStatus.FAILED for t in tasks):
            if any(t.status == ReviewTaskStatus.COMPLETED for t in tasks):
                review_job.status = ReviewJobStatus.PARTIAL_SUCCESS
            else:
                review_job.status = ReviewJobStatus.FAILED

            review_job.completed_at = datetime.now(timezone.utc)

        await db.commit()


async def review_worker() -> None:
    while True:
        try:
            message: ReviewTaskMessage = await queue_provider.consume(
                ReviewQueue.REVIEW,
            )

            await process_review_task(message)

        except Exception as ex:
            print("REVIEW WORKER ERROR")
            print(ex)

            await asyncio.sleep(1)
