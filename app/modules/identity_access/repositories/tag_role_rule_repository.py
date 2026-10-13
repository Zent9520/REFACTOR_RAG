from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.modules.identity_access.models.tag_role_rule import TagRoleRule

class TagRoleRuleRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        tag_id: int,
        role_id: int,
    ):
        rule = TagRoleRule(
            tag_id=tag_id,
            role_id=role_id,
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        return rule
    
    @staticmethod
    async def get_all(
        db: AsyncSession
    ):
        result = await db.execute(
            select(TagRoleRule)
        )
        return result.scalars().all()