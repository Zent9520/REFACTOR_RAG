from uuid import UUID

from sqlalchemy import (
    select
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from backend.app.models.recruitment.recruitment_candidate import (
    RecruitmentCandidate
)


class RecruitmentCandidateRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        campaign_id: UUID,
        candidate_name: str | None,
        file_name: str,
        file_path: str,
        file_size: int | None = None,
        mime_type: str | None = None
    ):
        item = RecruitmentCandidate(
            campaign_id=campaign_id,
            candidate_name=candidate_name,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type
        )

        db.add(item)

        await db.commit()

        await db.refresh(item)

        return item

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        id: UUID
    ):
        query = await db.execute(
            select(
                RecruitmentCandidate
            )
            .where(
                RecruitmentCandidate.id == id
            )
        )

        return (
            query
            .scalar_one_or_none()
        )

    @staticmethod
    async def get_by_campaign(
        db: AsyncSession,
        campaign_id: UUID
    ):
        query = await db.execute(
            select(
                RecruitmentCandidate
            )
            .where(
                RecruitmentCandidate.campaign_id == campaign_id
            )
            .order_by(
                RecruitmentCandidate.created_at.asc()
            )
        )

        return (
            query
            .scalars()
            .all()
        )
