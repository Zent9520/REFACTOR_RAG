from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.modules.identity_access.models.tag import Tag

class TagRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        description: str | None,
        sensitivity_level: int,
    ):
        tag = Tag(
            name=name,
            description=description,
            sensitivity_level=sensitivity_level,
        )
        db.add(tag)
        
        await db.commit()
        await db.refresh(tag)
        
        return tag
    
    @staticmethod
    async def get_all(
        db: AsyncSession
    ):
        result = await db.execute(
            select(Tag)
        )
        return result.scalars().all()
    
    