from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from sqlalchemy import (
    select
)

from backend.app.modules.chat.models.user_memories import (
    UserMemory
)

from backend.app.modules.chat.enums.memories import (
    MemoryType
)

class UserMemoryRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        user_email: str,
        memory_type: MemoryType,
        memory_text:str,
        importance: int = 5,
        
        
    ):
        item = UserMemory(

            user_email=user_email,

            memory_type=memory_type,

            memory_text=memory_text,

            importance=importance

        ) 
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item
    @staticmethod
    async def get_by_user_email(db: AsyncSession, user_email: str):
        query = await db.execute(
                select(
                    UserMemory
                )
                .where(
                    UserMemory.email == user_email
                )
                .order_by(
                    UserMemory.importance.desc()
                    
                )
        
        )
        return (
                query.scalars().all()
            )
    @staticmethod
    async def delete(db: AsyncSession, id: str):
        query = await db.execute(
            select (
                UserMemory
                
            )
            .where(
                UserMemory.id == id
            )
        )
        item = query.scalar_one_or_none()
        if not item:
         return False
        
        await db.delete(item)
        await db.commit()
        return True