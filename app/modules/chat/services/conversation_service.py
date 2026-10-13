from backend.app.modules.chat.repositories.conversation_repository import (

 ConversationRepository

)
from uuid import UUID
class ConversationService:
    @staticmethod
    async def create(
        db,
        conversation_id: UUID,
        title: str,
        email: str | None = None
    ):
     return await (
         ConversationRepository.create(
             db,
             conversation_id=conversation_id,
             title=title,
             email=email,
        
         )
     )
    
    @staticmethod
    async def get_all(
        db,
        email
    ):
        return await (
            ConversationRepository.get_by_email(
                db,
                email
            )
        )
    @staticmethod
    async def delete(
        db,
        id
    ):
        return await (
            ConversationRepository.delete(db, id)
        )
    
    @staticmethod
    async def rename(
        db,
        id,
        title
    ):
        return await (
            ConversationRepository.rename(db, id, title)
        )
    @staticmethod
    async def get_or_create_by_email(
        db,
        email
    ):
        return await (
            ConversationRepository
            .get_or_create_by_email(
                db,
                email
            )
        )