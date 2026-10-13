# app/repositories/meeting_transcript_repository.py

from sqlalchemy import (
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.meeting.models.meeting_transcript import (
    MeetingTranscript,
)


class MeetingTranscriptRepository:

    @staticmethod
    async def get_by_transcript_id(
        db: AsyncSession,
        transcript_id: str,
    ):
        result = await db.execute(
            select(MeetingTranscript)
            .where(
                MeetingTranscript.transcript_id == transcript_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_meeting_id(
        db: AsyncSession,
        meeting_id,
    ):
        result = await db.execute(
            select(MeetingTranscript)
            .where(
                MeetingTranscript.meeting_id == meeting_id
            )
        )

        return list(
            result.scalars().all()
        )

    @staticmethod
    async def create(
        db: AsyncSession,
        model: MeetingTranscript,
    ):
        db.add(model)