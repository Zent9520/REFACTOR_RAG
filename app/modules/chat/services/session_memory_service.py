from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from backend.app.modules.chat.repositories.message_repository import (
    MessageRepository
)

class SessionMemoryService:
    @staticmethod
    async def build_context(
        db: AsyncSession,
        conversation_id: str,
    ):
        recent_messages = await(
            MessageRepository
            .get_recent_message(
                db=db,
                conversation_id= conversation_id,
                limit=3
            )
            
        )
        formatted_messages = []

        for message in recent_messages:

            if message.role != "user":
                continue

            formatted_messages.append(
                message.content
            )

        return "\n".join(
            formatted_messages
        )
        
    @staticmethod
    async def build_retrieval_query (
        db: AsyncSession,
        conversation_id: str,
        question: str
        
    ):
        messages = await(
            MessageRepository
            .get_recent_message(
                db=db,
                conversation_id=conversation_id,
                limit=5
            )
            
           
            
            
        )
        user_messages = []
        for msg in messages:
            if msg.role != "user":
                continue
            user_messages.append(
                msg.content
            )
        history = "\n".join(
            user_messages[-3:]
        )
        return f""" 
    {history}
    
    {question}
    
    
    
    """
                
        
                 
            