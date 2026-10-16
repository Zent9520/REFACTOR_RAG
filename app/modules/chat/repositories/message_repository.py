from sqlalchemy.ext.asyncio import (

 AsyncSession

)

from sqlalchemy import (

 select

)

from backend.app.modules.chat.models.messages import (

 Message

)
from sqlalchemy import func 


class MessageRepository:
    @staticmethod
    async def create(db, payload, *, refresh: bool = True):
        item = Message(**payload)
        db.add(item)
        await db.commit()
        if refresh:
            await db.refresh(item)
        return item
    @staticmethod
    async def get_by_conversation(
        db,
        conversation_id
    ):
        query = await db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id
            )
        )
        
        return (

   query

   .scalars()

   .all()

  )
    @staticmethod
    async def get_recent_message(db: AsyncSession, conversation_id: str, limit: int ):
        query = await db.execute(
            select(
                Message
            )
            .where(
                Message.conversation_id == conversation_id,
                Message.role == "user"
                
                
            )
            .order_by(
                Message.created_at.desc()
            )
            .limit(limit)
        )
        messages = (
            query.scalars().all()
            
        )
        return list(
            reversed(messages)
            
        )
        
    @staticmethod
    async def count_by_conversation(
        db: AsyncSession,
        conversation_id: str
    ):

        query = await db.execute(

            select(
                func.count(Message.id)
            )

            .where(
                Message.conversation_id
                ==
                conversation_id
            )

        )

        return query.scalar()
    @staticmethod
    async def get_messages_after_offset(
        db: AsyncSession,
        conversation_id: str,
        offset: int,
        limit: int
    ):

        query = await db.execute(

            select(
                Message
            )

            .where(
                Message.conversation_id
                ==
                conversation_id
            )

            .order_by(
                Message.created_at.asc()
            )

            .offset(offset)

            .limit(limit)

        )

        return (

            query

            .scalars()

            .all()

        )
            
        
        