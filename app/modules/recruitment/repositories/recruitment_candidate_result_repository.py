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

from backend.app.models.recruitment.recruitment_candidate_result import (
    RecruitmentCandidateResult
)


class RecruitmentCandidateResultRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        candidate_id: UUID,
        model: str,
        score,
        summary: str | None,
        strengths,
        weaknesses,
        assessment: str | None,
        reason: str | None,
        raw_response,
    ):
        item = RecruitmentCandidateResult(
            candidate_id=candidate_id,
            model=model,
            score=score,
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            assessment=assessment,
            reason=reason,
            raw_response=raw_response,
        )

        db.add(item)

        await db.commit()

        await db.refresh(item)

        return item
    
    @staticmethod
    async def get_by_candidate(
        db: AsyncSession,
        candidate_id: UUID,
    ):
        query = await db.execute(
            select(
                RecruitmentCandidateResult
            )
            .where(
                RecruitmentCandidateResult.candidate_id == candidate_id
            )
        )

        return (
            query
            .scalar_one_or_none()
        )