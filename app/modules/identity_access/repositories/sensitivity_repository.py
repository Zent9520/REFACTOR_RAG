from sqlalchemy import select

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from backend.app.modules.identity_access.models.sensitivity_level import (
    SensitivityLevel
)


class SensitivityRepository:


    @staticmethod
    async def get_all(

        db: AsyncSession

    ):


        result = await db.execute(

            select(
                SensitivityLevel
            )

        )


        return (
            result.scalars()
            .all()
        )