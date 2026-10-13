from sqlalchemy import (
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.identity_access.models.department import (
    Department,
)


class DepartmentRepository:

    @staticmethod
    async def get_all(
        db: AsyncSession,
    ) -> list[Department]:

        result = await db.execute(
            select(Department)
            .order_by(Department.name)
        )

        return result.scalars().all()