from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from sqlalchemy import (
    select
)

from backend.app.modules.chat.models.conversation_summary import (
    ConversationSummary
)

from uuid import UUID
from datetime import datetime


class ConversationSummaryRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        conversation_id: UUID,
        summary: str,
        last_processed_message_count: int = 0
    ):

        item = ConversationSummary(

            conversation_id=conversation_id,

            summary=summary,

            last_processed_message_count=
            last_processed_message_count

        )

        db.add(item)

        await db.commit()

        await db.refresh(item)

        return item

    @staticmethod
    async def get_by_conversation_id(
        db: AsyncSession,
        conversation_id: UUID
    ):
        query = await db.execute(

            select(
                ConversationSummary
            )

            .where(
                ConversationSummary.conversation_id
                ==
                conversation_id
            )

        )

        return query.scalar_one_or_none()

    @staticmethod
    async def update(
        db: AsyncSession,
        conversation_id: UUID,
        summary: str,
        last_processed_message_count: int
    ):

        query = await db.execute(

            select(
                ConversationSummary
            )

            .where(
                ConversationSummary.conversation_id
                ==
                conversation_id
            )

        )

        item = query.scalar_one_or_none()

        if not item:
            return None

        item.summary = summary

        item.last_processed_message_count = (
            last_processed_message_count
        )
        item.updated_at = datetime.now()

        await db.commit()

        await db.refresh(item)

        return item

    @staticmethod
    async def delete(
    db: AsyncSession,
    conversation_id: UUID
):
        query = await db.execute(

            select(
                ConversationSummary
            )

            .where(
                ConversationSummary.conversation_id
                ==
                conversation_id
            )

        )

        item = query.scalar_one_or_none()

        if not item:
            return False

        await db.delete(item)

        await db.commit()

        return True