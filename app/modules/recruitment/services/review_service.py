from sqlalchemy.ext.asyncio import AsyncSession

from app.core.not_found_exception import (
    NotFoundException,
)

from backend.app.modules.recruitment.enums.review_job_status import (
    ReviewJobStatus,
)

from backend.app.modules.recruitment.enums.review_task_status import (
    ReviewTaskStatus,
)

from backend.app.modules.recruitment.schemas.create_review_request import (
    CreateReviewRequest,
)

from backend.app.modules.recruitment.schemas.review_dto import (
    ReviewResponse,
    ReviewFileResponse,
)

from backend.app.modules.recruitment.models.review_job import (
    ReviewJob,
)

from backend.app.modules.recruitment.models.review_task import (
    ReviewTask,
)

from backend.app.modules.configuration.repositories.ai_model_repository import (
    AIModelRepository,
)

from backend.app.modules.recruitment.repositories.review_job_repository import (
    ReviewJobRepository,
)

from backend.app.modules.recruitment.repositories.review_task_repository import (
    ReviewTaskRepository,
)

from backend.app.modules.recruitment.services.review_ai_service import (
    ReviewAIService,
)

from backend.app.modules.recruitment.services.temp_file_service import (
    TempFileService,
)

from datetime import (
    datetime,
    timezone,
)




class ReviewService:

    @staticmethod
    async def create_review(
        db: AsyncSession,
        request: CreateReviewRequest,
        created_by=None,
    ) -> ReviewResponse:

        # =====================================
        # Validate AI Model
        # =====================================

        model = await (
            AIModelRepository.get_by_id(
                db=db,
                id=request.model_id,
            )
        )

        if model is None:

            raise NotFoundException(
                "AI Model not found.",
            )

        # =====================================
        # Create Review Job
        # =====================================

        review_job = ReviewJob(
            model_id=model.id,

            job_description=request.job_description,

            status=ReviewJobStatus.QUEUED,

            total_files=len(
                request.files,
            ),

            created_by=created_by,

        )

        await (
            ReviewJobRepository.create(
                db=db,
                review_job=review_job,
            )
        )

        await db.flush()

        review_tasks: list[ReviewTask] = []

        # =====================================
        # Save Temp Files + Create Tasks
        # =====================================

        try:

            for file in request.files:

                temp_file = await (
                    TempFileService.save(
                        job_id=review_job.id,
                        file=file,
                    )
                )

                review_task = ReviewTask(

                    job_id=review_job.id,

                    status=ReviewTaskStatus.QUEUED,

                    file_name=file.filename,

                    file_path=temp_file.file_path,

                    file_size=temp_file.file_size,

                    mime_type=file.content_type or "",

                )

                await (
                    ReviewTaskRepository.create(
                        db=db,
                        review_task=review_task,
                    )
                )

                review_tasks.append(
                    review_task,
                )

            await db.commit()

        except Exception:

            await db.rollback()

            TempFileService.delete_job_directory(
                review_job.id,
            )

            raise
        
        
        
                # =====================================
        # Process Review
        # =====================================

        results: list[ReviewFileResponse] = []

        completed_files = 0

        failed_files = 0

        review_job.status = (
            ReviewJobStatus.PROCESSING
        )

        review_job.started_at = (
            datetime.now(timezone.utc)
        )

        await db.commit()

        for review_task in review_tasks:

            try:

                review_task.status = (
                    ReviewTaskStatus.PROCESSING
                )

                review_task.started_at = (
                    datetime.now(timezone.utc)
                )

                await db.commit()

                ai_result = await (
                    ReviewAIService.execute(
                        db=db,
                        model_id=review_job.model_id,
                        job_description=review_job.job_description,
                        file_path=review_task.file_path,
                    )
                )

                result = ai_result.review_result

                extraction = ai_result.extraction

                review_task.review_result = result
                
                
                review_task.file_name = (
                    result.get("candidate_name")
                )
                review_task.status = (
                    ReviewTaskStatus.COMPLETED
                )

                review_task.completed_at = (
                    datetime.now(timezone.utc)
                )

                completed_files += 1

                await db.commit()

            except Exception as ex:

                review_task.status = (
                    ReviewTaskStatus.FAILED
                )

                review_task.error_message = (
                    str(ex)
                )

                review_task.completed_at = (
                    datetime.now(timezone.utc)
                )

                failed_files += 1

                await db.commit()

                result = None

                extraction = None

            results.append(

                ReviewFileResponse(

                    task_id=review_task.id,

                    file_name=review_task.file_name,

                    status=review_task.status,

                    review_result=result,

                    extraction=extraction,

                )

            )

        # =====================================
        # Update Job Status
        # =====================================

        if failed_files == 0:

            review_job.status = (
                ReviewJobStatus.COMPLETED
            )

        elif completed_files == 0:

            review_job.status = (
                ReviewJobStatus.FAILED
            )

        else:

            review_job.status = (
                ReviewJobStatus.PARTIAL_SUCCESS
            )

        review_job.completed_at = (
            datetime.now(timezone.utc)
        )

        await db.commit()

        # =====================================
        # Response
        # =====================================

        return ReviewResponse(

            job_id=review_job.id,

            status=review_job.status,

            total_files=review_job.total_files,

            results=results,

        )

      
