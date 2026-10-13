from sqlalchemy.ext.asyncio import (

 AsyncSession

)

from sqlalchemy import (

 select

)
from uuid import UUID
from typing import Optional

from backend.app.modules.chat.models.conversation import (
    

 Conversation
 

)


class ConversationRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        conversation_id: UUID,
        title: str,
        email: Optional[str] = None,
        
    ):
     item = Conversation( 
                         
        id=conversation_id,
                         
        title=title,
                         
        user_email = email  
                         )
     db.add(item)
     await db.commit()
     await db.refresh(item)
     return item
    
    
    @staticmethod
    async def get_by_email(
        db: AsyncSession,
        email: str,
        
    ):
        query = await db.execute(
        select(
            Conversation
        )
        .where(
            Conversation.user_email == email
        )
    )
        return (

        query

        .scalars()

        .all()

        )
        
    @staticmethod
    async def rename(
        db: AsyncSession,
        id,
        title: str
        
    ):
        query = await db.execute(
            select(
                Conversation
            )
            .where(
                Conversation.id == id
            )
        )
        item = query.scalar_one_or_none()
        if not item:
            return None
        item.title = title
        
        await db.commit()
        await db.refresh(item)
        return item
    @staticmethod
    async def delete(

        db:AsyncSession,

        id

        ):


        query= await db.execute(

        select(

            Conversation

        )

        .where(

            Conversation.id

            ==

            id

        )

        )


        item=query.scalar_one_or_none()


        if not item:

            return False


        await db.delete(

        item

        )


        await db.commit()


        return True
    
    @staticmethod
    async def get_or_create_by_email(
        db: AsyncSession,
        email: str
    ):

        query = await db.execute(
            select(
                Conversation
            )
            .where(
                Conversation.user_email == email
            )
            .order_by(
                Conversation.created_at.asc()
            )
        )

        item = query.scalar_one_or_none()

        if item:
            return item

        item = Conversation(
            user_email=email
        )

        db.add(item)

        await db.commit()

        await db.refresh(item)

        return item
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        conversation_id: UUID,
    ) -> Conversation | None:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id
            )
        )

        return result.scalar_one_or_none()

                