from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.modules.identity_access.models.role import Role

class RoleRepository:
    
    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        description: str | None = None
    ):
        role = Role(
            name=name,
            description=description
        )
        
        db.add(role)
        await db.commit()
        await db.refresh(role)
        
        
        return role
    
    @staticmethod
    async def get_all(db: AsyncSession ):
        result = await db.execute(
            select(Role)
        )
        return result.scalars().all()
    @staticmethod
    async def get_role_names(
        db: AsyncSession
    ) -> list[str]:

        result = await db.execute(
            select(Role.name)
        )

        return [
            row[0]
            for row in result.all()
        ]
        


    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        role_id: int,
    ) -> str | None:

        result = await db.execute(
            select(Role.name)
            .where(
                Role.id == role_id
            )
        )

        return result.scalar_one_or_none()
        