from sqlalchemy import (
   
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.executive_data.models.executive_data_dashboard import (
    ExecutiveDataDashboard,
)

from backend.app.modules.executive_data.models.executive_data_raw import (
    ExecutiveDataRaw,
)
from uuid import UUID


class ExecutiveDataRepository:

    # ===================================================
    # RAW
    # ===================================================

    @staticmethod
    async def create_raw(
        db: AsyncSession,
        item: ExecutiveDataRaw,
    ) -> None:

        db.add(item)

    @staticmethod
    async def update_raw(
        db: AsyncSession,
        item: ExecutiveDataRaw,
    ) -> None:

        db.add(item)

    @staticmethod
    async def get_raw_by_file_hash(
        db: AsyncSession,
        file_hash: str,
    ) -> ExecutiveDataRaw | None:

        query = await db.execute(

            select(
                ExecutiveDataRaw,
            )

            .where(
                ExecutiveDataRaw.file_hash
                == file_hash,
            )

        )

        return query.scalar_one_or_none()

    @staticmethod
    async def get_raw_by_id(
        db: AsyncSession,
        dataset_id,
    ) -> ExecutiveDataRaw | None:

        query = await db.execute(

            select(
                ExecutiveDataRaw,
            )

            .where(
                ExecutiveDataRaw.id
                == dataset_id,
            )

        )

        return query.scalar_one_or_none()

    @staticmethod
    async def delete_raw(
        db: AsyncSession,
        item: ExecutiveDataRaw,
    ) -> None:

        await db.delete(item)

    # ===================================================
    # DASHBOARD
    # ===================================================

    @staticmethod
    async def create_dashboard(
        db: AsyncSession,
        item: ExecutiveDataDashboard,
    ) -> None:

        db.add(item)

    @staticmethod
    async def update_dashboard(
        db: AsyncSession,
        item: ExecutiveDataDashboard,
    ) -> None:

        db.add(item)

    @staticmethod
    async def get_dashboard_by_dataset_id(
        db: AsyncSession,
        dataset_id,
    ) -> ExecutiveDataDashboard | None:

        query = await db.execute(

            select(
                ExecutiveDataDashboard,
            )

            .where(
                ExecutiveDataDashboard.dataset_id
                == dataset_id,
            )

        )

        return query.scalar_one_or_none()

    @staticmethod
    async def delete_dashboard(
        db: AsyncSession,
        item: ExecutiveDataDashboard,
    ) -> None:

        await db.delete(item)
        
        
    @staticmethod
    async def get_dataset_summaries(
        db: AsyncSession,
    ):

        query = await db.execute(

            select(

                ExecutiveDataRaw.id,

                ExecutiveDataRaw.dataset_name,

                ExecutiveDataDashboard.summary,

            )

            .join(

                ExecutiveDataDashboard,

                ExecutiveDataDashboard.dataset_id
                == ExecutiveDataRaw.id,

            )

            .order_by(

                ExecutiveDataRaw.dataset_name.asc(),

            )

        )

        return [

            {

                "id": row.id,

                "dataset_name": row.dataset_name,

                "summary": row.summary,

            }

            for row in query.all()

        ]
        
    @staticmethod
    async def get_report_data(
        db: AsyncSession,
        dataset_id: UUID,
    ):

        query = await db.execute(

            select(

                ExecutiveDataRaw.report_data,

            )

            .where(

                ExecutiveDataRaw.id
                == dataset_id,

            )

        )

        return query.scalar_one_or_none()
    
    @staticmethod
    async def get_report_data_list(
        db: AsyncSession,
        dataset_ids: list[UUID],
    ):

        query = await db.execute(

            select(

                ExecutiveDataRaw.report_data,

            )

            .where(

                ExecutiveDataRaw.id.in_(

                    dataset_ids,

                )

            )

        )

        return [

            row.report_data

            for row in query.all()

        ]
        
    @staticmethod
    async def get_datasets(
        db: AsyncSession,
    ):

        query = await db.execute(

            select(

                ExecutiveDataRaw,

                ExecutiveDataDashboard,

            )

            .join(

                ExecutiveDataDashboard,

                ExecutiveDataDashboard.dataset_id
                == ExecutiveDataRaw.id,

            )

            .order_by(

                ExecutiveDataRaw.created_at.desc(),

            )

        )

        return query.all()
    
    
    @staticmethod
    async def get_source_files(
        db: AsyncSession,
    ) -> list[str]:

        query = await db.execute(

            select(

                ExecutiveDataRaw.source_file,

            )

        )

        return list(
            query.scalars().all()
        )