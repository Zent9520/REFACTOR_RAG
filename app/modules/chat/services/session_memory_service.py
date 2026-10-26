from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.modules.chat.repositories.message_repository import (
    MessageRepository
)

class SessionMemoryService:
    @staticmethod
    async def get_recent_user_questions(
        db: AsyncSession,
        conversation_id: str,
    ) -> list[str]:
        messages = await MessageRepository.get_recent_message(
            db=db, conversation_id=conversation_id, limit=3
        )
        return [message.content for message in messages if message.role == "user"]

    @staticmethod
    def history_after_question(recent_questions: list[str], question: str) -> str:
        """Mirror the latest-three-user-messages query after saving question."""
        return "\n".join((recent_questions + [question])[-3:])

    @staticmethod
    async def build_context(
        db: AsyncSession,
        conversation_id: str,
    ):
        return "\n".join(await SessionMemoryService.get_recent_user_questions(
            db=db, conversation_id=conversation_id
        ))
        
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
                
        
                 
            
