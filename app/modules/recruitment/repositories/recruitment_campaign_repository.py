from uuid import UUID

from sqlalchemy import (
    select,
    update
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from backend.app.models.recruitment.recruitment_campaign import (
    RecruitmentCampaign
)




from backend.app.models.recruitment.review_job import (
    ReviewJob,
)

from backend.app.models.recruitment.review_task import (
    ReviewTask,
)



class RecruitmentCampaignRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        role_id: int,
        title: str,
        job_description: str,
        created_by: UUID | None = None
    ):
        item = RecruitmentCampaign(
            role_id=role_id,
            title=title,
            job_description=job_description,
            created_by=created_by,
            cv_embedding=None,
            cv_data=None
        )

        db.add(item)

        await db.commit()

        await db.refresh(item)

        return item

    @staticmethod
    async def get_all(
        db: AsyncSession
    ):
        query = await db.execute(
            select(
                RecruitmentCampaign
            )
            .order_by(
                RecruitmentCampaign.created_at.desc()
            )
        )

        return (
            query
            .scalars()
            .all()
        )

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        id: UUID
    ):
        query = await db.execute(
            select(
                RecruitmentCampaign
            )
            .where(
                RecruitmentCampaign.id == id
            )
        )

        return (
            query
            .scalar_one_or_none()
        )
        
        
    @staticmethod
    async def update_cv_embedding(
        db: AsyncSession,
        campaign_id: UUID,
        cv_embedding: list[float],
    ):

        query = await db.execute(

            update(
                RecruitmentCampaign
            )

            .where(

                RecruitmentCampaign.id
                == campaign_id,

            )

            .values(

                cv_embedding=
                cv_embedding,

            )

            .returning(
                RecruitmentCampaign
            )

        )

        item = (
            query
            .scalar_one_or_none()
        )

        if item is not None:

            await db.commit()

        return item
    
    
    @staticmethod
    async def update_cv_data(
        db: AsyncSession,
        campaign_id: UUID,
        cv: dict,
    ):

        query = await db.execute(

            select(
                RecruitmentCampaign
            )

            .where(
                RecruitmentCampaign.id
                == campaign_id
            )

        )

        campaign = (
            query
            .scalar_one_or_none()
        )

        if campaign is None:

            return None

        current_data = (
            campaign.cv_data
            or {
                "candidates": []
            }
        )

        candidates = (
            current_data
            .get(
                "candidates",
                []
            )
        )

        candidates.append(
            cv
        )

        campaign.cv_data = {
            "candidates": candidates
        }

        await db.commit()

        await db.refresh(
            campaign
        )

        return campaign
    
    async def get_data_cv(
        
     db: AsyncSession,
     campaign_id: UUID
        
    ):
        
        query = await db.execute(
                    select(
                        RecruitmentCampaign.cv_data
                    )
                    .where(
                        RecruitmentCampaign.id == campaign_id
                    )
                )
        
        return (
                    query
                    .scalar_one_or_none()
                )
        
    @staticmethod
    async def get_all(
        db: AsyncSession,
    ):

        query = await db.execute(

            select(
                RecruitmentCampaign,
            )

            .order_by(
                RecruitmentCampaign.created_at.desc()
            )

        )

        return (
            query
            .scalars()
            .all()
        )
        
    
    @staticmethod
    async def get_candidates(
        db: AsyncSession,
        campaign_id: UUID,
    ):

        query = await db.execute(

            select(
                ReviewTask,
            )

            .join(
                ReviewJob,
                ReviewJob.id
                == ReviewTask.job_id,
            )

            .where(
                ReviewJob.campaign_id
                == campaign_id,
            )
            .order_by(
                ReviewTask.created_at.asc()
            )

        )

        return (
            query
            .scalars()
            .all()
        )
        
    
    @staticmethod
    async def get_candidate(
        db: AsyncSession,
        campaign_id: UUID,
        task_id: UUID,
    ):

        query = await db.execute(

            select(
                ReviewTask,
            )

            .join(
                ReviewJob,
                ReviewJob.id
                == ReviewTask.job_id,
            )
            
            .where(

                ReviewJob.campaign_id
                == campaign_id,

                ReviewTask.id
                == task_id,

            )

        )

        return (
            query
            .scalar_one_or_none()
        )
        