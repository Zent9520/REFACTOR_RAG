from sqlalchemy import (
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.project_tracking.models.project_tracking_dashboard import (
    ProjectTrackingDashboard,
)


class ProjectTrackingDashboardRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        item: ProjectTrackingDashboard,
    ) -> None:

        db.add(item)

    @staticmethod
    async def update(
        db: AsyncSession,
        item: ProjectTrackingDashboard,
    ) -> None:

        db.add(item)

    @staticmethod
    async def get_by_project_code(
        db: AsyncSession,
        project_code: str,
    ) -> ProjectTrackingDashboard | None:

        query = await db.execute(

            select(
                ProjectTrackingDashboard,
            )

            .where(
                ProjectTrackingDashboard.project_code
                == project_code,
            )

        )

        return query.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
    ) -> list[ProjectTrackingDashboard]:

        query = await db.execute(

            select(
                ProjectTrackingDashboard,
            )

            .order_by(
                ProjectTrackingDashboard.project_code.asc(),
            )

        )

        return list(
            query.scalars().all()
        )

    @staticmethod
    async def delete(
        db: AsyncSession,
        item: ProjectTrackingDashboard,
    ) -> None:

        await db.delete(item)