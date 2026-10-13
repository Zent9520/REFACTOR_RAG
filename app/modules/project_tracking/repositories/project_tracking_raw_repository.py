from sqlalchemy import (
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.project_tracking.models.project_tracking_raw import (
    ProjectTrackingRaw,
)

from sqlalchemy import (
    select,
)

from backend.app.modules.project_tracking.models.project_tracking_dashboard import (
    ProjectTrackingDashboard,
)


class ProjectTrackingRawRepository:

    @staticmethod
    async def create(
        db: AsyncSession,
        item: ProjectTrackingRaw,
    ) -> None:

        db.add(item)

    @staticmethod
    async def update(
        db: AsyncSession,
        item: ProjectTrackingRaw,
    ) -> None:

        db.add(item)

    @staticmethod
    async def get_by_project_code(
        db: AsyncSession,
        project_code: str,
    ) -> ProjectTrackingRaw | None:

        query = await db.execute(

            select(
                ProjectTrackingRaw,
            )

            .where(
                ProjectTrackingRaw.project_code
                == project_code,
            )

        )

        return query.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
    ) -> list[ProjectTrackingRaw]:

        query = await db.execute(

            select(
                ProjectTrackingRaw,
            )

            .order_by(
                ProjectTrackingRaw.project_code.asc(),
            )

        )

        return list(
            query.scalars().all()
        )

    @staticmethod
    async def delete(
        db: AsyncSession,
        item: ProjectTrackingRaw,
    ) -> None:

        await db.delete(item)
        
        
    @staticmethod
    async def get_dashboard_projects(
        db: AsyncSession,
    ):

        query = await db.execute(

            select(

                ProjectTrackingRaw,

                ProjectTrackingDashboard,

            )

            .join(

                ProjectTrackingDashboard,

                ProjectTrackingRaw.project_code
                ==
                ProjectTrackingDashboard.project_code,

            )

            .order_by(

                ProjectTrackingRaw.project_name.asc(),

            )

        )

        return query.all()
    
    @staticmethod
    async def get_dashboard_project(
        db: AsyncSession,
        project_code: str,
    ):

        query = await db.execute(

            select(

                ProjectTrackingRaw,

                ProjectTrackingDashboard,

            )

            .join(

                ProjectTrackingDashboard,

                ProjectTrackingRaw.project_code
                ==
                ProjectTrackingDashboard.project_code,

            )

            .where(

                ProjectTrackingRaw.project_code
                == project_code,

            )

        )

        return query.first()
    
    @staticmethod
    async def get_project_names(
        db: AsyncSession,
    ) -> list[dict]:

        query = await db.execute(

            select(

                ProjectTrackingRaw.project_code,

                ProjectTrackingRaw.project_name,

            )

            .order_by(

                ProjectTrackingRaw.project_name.asc(),

            )

        )

        return [

            {

                "project_code": row.project_code,

                "project_name": row.project_name,

            }

            for row in query.all()

        ]
    
    @staticmethod
    async def get_by_project_codes(
        db: AsyncSession,
        project_codes: list[str],
    ) -> list[ProjectTrackingRaw]:

        query = await db.execute(

            select(
                ProjectTrackingRaw,
            )

            .where(
                ProjectTrackingRaw.project_code.in_(
                    project_codes,
                ),
            )

            .order_by(
                ProjectTrackingRaw.project_name.asc(),
            )

        )

        return list(
            query.scalars().all(),
        )
    @staticmethod
    async def get_all_project_data(
        db: AsyncSession,
    ) -> list[ProjectTrackingRaw]:

        query = await db.execute(

            select(
                ProjectTrackingRaw,
            )

            .order_by(
                ProjectTrackingRaw.project_name.asc(),
            )

        )

        return list(
            query.scalars().all(),
        )
    
        
    
    