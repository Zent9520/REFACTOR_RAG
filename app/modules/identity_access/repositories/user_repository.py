from uuid import UUID

from sqlalchemy import (
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.identity_access.models.user_model import (
    User,
)


class UserRepository:

    @staticmethod
    async def get_by_email(
        db: AsyncSession,
        email: str,
    ):
        query = await db.execute(
            select(User).where(
                User.email == email,
            )
        )

        return query.scalar_one_or_none()

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        id: UUID,
    ):
        query = await db.execute(
            select(User).where(
                User.id == id,
            )
        )

        return query.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        user: User,
    ):
        db.add(user)

        await db.commit()

        await db.refresh(user)

        return user
    
    @staticmethod
    async def update(
        db: AsyncSession,
        user: User,
    ):
        await db.commit()

        await db.refresh(
            user,
        )

        return user
    
