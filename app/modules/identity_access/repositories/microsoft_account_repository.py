from uuid import UUID

from sqlalchemy import (
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.identity_access.models.microsoft_account import (
    MicrosoftAccount,
)


class MicrosoftAccountRepository:

    @staticmethod
    async def get_by_user_id(
        db: AsyncSession,
        user_id: UUID,
    ):
        query = await db.execute(
            select(MicrosoftAccount).where(
                MicrosoftAccount.user_id == user_id,
            )
        )

        return query.scalar_one_or_none()

    @staticmethod
    async def get_by_object_id(
        db: AsyncSession,
        object_id: UUID,
    ):
        query = await db.execute(
            select(MicrosoftAccount).where(
                MicrosoftAccount.object_id == object_id,
            )
        )

        return query.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        account: MicrosoftAccount,
    ):
        db.add(account)

        await db.commit()

        await db.refresh(account)

        return account
    
    @staticmethod
    async def update(
        db: AsyncSession,
        account: MicrosoftAccount,  
    ):
        await db.commit()

        await db.refresh(
            account,
        )

        return account