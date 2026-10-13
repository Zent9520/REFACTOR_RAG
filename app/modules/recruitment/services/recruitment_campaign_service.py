from uuid import UUID

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.not_found_exception import (
    NotFoundException,
)

from backend.app.repositories.recruitment.recruitment_campaign_repository import (
    RecruitmentCampaignRepository,
)

from backend.app.schemas.recruitment.recruitment_schema import (
    RecruitmentCampaignResponse,
    RecruitmentCandidateResponse,
    RecruitmentCandidateDetailResponse,
)


class RecruitmentCampaignService:

    # ==========================================================
    # LIST CAMPAIGNS
    # ==========================================================

    @staticmethod
    async def get_list(
        db: AsyncSession,
    ):

        campaigns = await (
            RecruitmentCampaignRepository
            .get_all(
                db=db,
            )
        )

        results = []

        for campaign in campaigns:

            cv_data = (
                campaign.cv_data
                or {
                    "candidates": []
                }
            )

            candidates = (
                cv_data
                .get(
                    "candidates",
                    []
                )
            )

            results.append({

                "id":
                campaign.id,

                "title":
                campaign.title,

                "role_id":
                campaign.role_id,

                "job_description":
                campaign.job_description,

                "status":
                campaign.status,

                "total_candidates":
                len(candidates),

                "created_at":
                campaign.created_at,

                "updated_at":
                campaign.updated_at,

            })

        return results

    # ==========================================================
    # CAMPAIGN DETAIL
    # ==========================================================

    @staticmethod
    async def get_detail(
        db: AsyncSession,
        campaign_id: UUID,
    ):

        campaign = await (
            RecruitmentCampaignRepository
            .get_by_id(
                db=db,
                id=campaign_id,
            )
        )

        if campaign is None:

            raise NotFoundException(
                "Recruitment campaign not found.",
            )

        tasks = await (
            RecruitmentCampaignRepository
            .get_candidates(
                db=db,
                campaign_id=campaign_id,
            )
        )

        candidates = []

        for task in tasks:

            result = (
                task.review_result
                or {}
            )

            candidates.append({

                "task_id":
                task.id,

                "file_name":
                task.file_name,

                "score":
                result.get("score"),

                "assessment":
                result.get("assessment"),

            })

        return {

            "id":
            campaign.id,

            "title":
            campaign.title,

            "role_id":
            campaign.role_id,

            "job_description":
            campaign.job_description,

            "status":
            campaign.status,

            "total_candidates":
            len(candidates),

            "created_at":
            campaign.created_at,

            "updated_at":
            campaign.updated_at,

            "candidates":
            candidates,

        }

    # ==========================================================
    # CANDIDATE DETAIL
    # ==========================================================

    @staticmethod
    async def get_candidate_detail(
        db: AsyncSession,
        campaign_id: UUID,
        task_id: UUID,
    ):

        task = await (
            RecruitmentCampaignRepository
            .get_candidate(
                db=db,
                campaign_id=campaign_id,
                task_id=task_id,
            )
        )

        if task is None:

            raise NotFoundException(
                "Candidate not found.",
            )

        result = (
            task.review_result
            or {}
        )

        return {

            "task_id":
            task.id,

            "campaign_id":
            campaign_id,

            "file_name":
            task.file_name,

            "score":
            result.get("score"),

            "assessment":
            result.get("assessment"),

            "reason":
            result.get("reason"),

            "summary":
            result.get("summary"),

            "strengths":
            result.get(
                "strengths",
                []
            ),

            "weaknesses":
            result.get(
                "weaknesses",
                []
            ),

            "review_result":
            result,

        }