from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.identity_access.tag import Tag
from backend.app.models.identity_access.role import Role
from backend.app.models.identity_access.tag_role_rule import TagRoleRule


class PolicyEngine:

    @staticmethod
    async def resolve_roles_from_tags(
        db: AsyncSession,
        tags: list[str]
    ) -> list[str]:

        stmt = (
            select(Role.name)
            .join(
                TagRoleRule,
                Role.id == TagRoleRule.role_id
            )
            .join(
                Tag,
                Tag.id == TagRoleRule.tag_id
            )
            .where(
                Tag.name.in_(tags)
            )
        )

        result = await db.execute(stmt)

        roles = result.scalars().all()

        # remove duplicates
        return list(set(roles))