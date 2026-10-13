# app/repositories/meeting_analysis_repository.py

from uuid import UUID

from sqlalchemy import (
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.meeting.models.meeting_analysis import (
    MeetingAnalysis,
)


class MeetingAnalysisRepository:

    @staticmethod
    async def get_by_event_id(
        db: AsyncSession,
        event_id: str,
    ):
        result = await db.execute(
            select(MeetingAnalysis)
            .where(
                MeetingAnalysis.event_id == event_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        id: UUID,
    ):
        result = await db.execute(
            select(MeetingAnalysis)
            .where(
                MeetingAnalysis.id == id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
    ):
        result = await db.execute(
            select(MeetingAnalysis)
            .order_by(
                MeetingAnalysis.start_time.desc()
            )
        )

        return list(
            result.scalars().all()
        )

    @staticmethod
    async def create(
        db: AsyncSession,
        model: MeetingAnalysis,
    ):
        db.add(model)

    @staticmethod
    async def update(
        db: AsyncSession,
        model: MeetingAnalysis,
    ):
        db.add(model)
        
    @staticmethod
    async def get_by_online_meeting_id(
        db: AsyncSession,
        online_meeting_id: str,
    ):
        result = await db.execute(
            select(MeetingAnalysis)
            .where(
                MeetingAnalysis.online_meeting_id
                == online_meeting_id
            )
        )

        return (
            result.scalar_one_or_none()
        ) 
        
    @staticmethod
    async def get_list(
        db: AsyncSession,
    ):

        result = await db.execute(
            select(
                MeetingAnalysis.id,
                MeetingAnalysis.subject,
                MeetingAnalysis.start_time,
                MeetingAnalysis.end_time,
            )
            .order_by(
                MeetingAnalysis.start_time.desc()
            )
        )

        return (
            result
            .mappings()
            .all()
        )

    @staticmethod
    async def get_detail(
        db: AsyncSession,
        id: UUID,
    ):

        result = await db.execute(
            select(
                MeetingAnalysis
            )
            .where(
                MeetingAnalysis.id == id
            )
        )

        return (
            result
            .scalar_one_or_none()
        )  