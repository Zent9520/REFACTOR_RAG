from sqlalchemy import (
    select
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy import delete

from backend.app.modules.configuration.models.ai_prompt import (
    AIPrompt
)
from uuid import UUID

from backend.app.modules.configuration.enums.prompt_code import PromptCode


class AIPromptRepository:

    @staticmethod
    async def get_by_code(
        db: AsyncSession,
        code: PromptCode,
    ):
        query = await db.execute(
            select(AIPrompt).where(
                AIPrompt.code == code.value,
                AIPrompt.is_active == True,
            )
        )

        return query.scalar_one_or_none()
        
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        id: UUID,
    ):
        query = await db.execute(
            select(
                AIPrompt
            )
            .where(
                AIPrompt.id == id,
                AIPrompt.is_active == True,
            )
        )

        return (
            query
            .scalar_one_or_none()
        )
    
    @staticmethod
    async def create(
        db: AsyncSession,
        prompt: AIPrompt,
        
    ) -> None:
        db.add(prompt)
        
    @staticmethod
    async def update(
        db: AsyncSession,
        prompt: AIPrompt,
        
    ) -> None:
        db.add(prompt)
        
        
    @staticmethod
    async def soft_delete(
        db: AsyncSession,
        prompt: AIPrompt,
    ) -> None:

        prompt.is_active = False
        db.add(prompt)
        
    @staticmethod
    async def get_all(
        db: AsyncSession,
    ) -> list[AIPrompt]:

        query = await db.execute(
            select(AIPrompt)
            .where(
                AIPrompt.is_active == True,
            )
            .order_by(
                AIPrompt.created_at.desc(),
            )
        )

        return list(
            query.scalars().all()
        )
        
        
    @staticmethod
    async def get_paged(
        db: AsyncSession,
        page: int,
        page_size: int,
    ) -> tuple[list[AIPrompt], int]:

        total = await db.scalar(
            select(func.count())
            .select_from(AIPrompt)
            .where(
                AIPrompt.is_active == True,
            )
        )

        query = await db.execute(
            select(AIPrompt)
            .where(
                AIPrompt.is_active == True,
            )
            .order_by(
                AIPrompt.created_at.desc(),
            )
            .offset(
                (page - 1) * page_size,
            )
            .limit(
                page_size,
            )
        )

        return (
            list(query.scalars().all()),
            total or 0,
        )
    
        
        
 