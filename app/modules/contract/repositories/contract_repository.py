from uuid import UUID

from sqlalchemy import (
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.contract.models.contract_raw import (
    ContractRaw,
)

from backend.app.modules.contract.models.contract_dashboard import (
    ContractDashboard,
)


class ContractRepository:

    # ==========================================================
    # Contract Raw
    # ==========================================================

    @staticmethod
    async def create_raw(
        db: AsyncSession,
        item: ContractRaw,
    ) -> None:

        db.add(item)

    @staticmethod
    async def update_raw(
        db: AsyncSession,
        item: ContractRaw,
    ) -> None:

        db.add(item)

    @staticmethod
    async def get_raw_by_id(
        db: AsyncSession,
        contract_id: UUID,
    ) -> ContractRaw | None:

        query = await db.execute(

            select(
                ContractRaw,
            )

            .where(
                ContractRaw.id == contract_id,
            )

        )

        return query.scalar_one_or_none()

    @staticmethod
    async def get_raw_by_hash(
        db: AsyncSession,
        file_hash: str,
    ) -> ContractRaw | None:

        query = await db.execute(

            select(
                ContractRaw,
            )

            .where(
                ContractRaw.file_hash == file_hash,
            )

        )

        return query.scalar_one_or_none()

    @staticmethod
    async def get_all_raw(
        db: AsyncSession,
    ) -> list[ContractRaw]:

        query = await db.execute(

            select(
                ContractRaw,
            )

            .order_by(
                ContractRaw.created_at.desc(),
            )

        )

        return list(
            query.scalars().all()
        )

    @staticmethod
    async def delete_raw(
        db: AsyncSession,
        item: ContractRaw,
    ) -> None:

        await db.delete(item)

    # ==========================================================
    # Contract Dashboard
    # ==========================================================

    @staticmethod
    async def create_dashboard(
        db: AsyncSession,
        item: ContractDashboard,
    ) -> None:

        db.add(item)

    @staticmethod
    async def update_dashboard(
        db: AsyncSession,
        item: ContractDashboard,
    ) -> None:

        db.add(item)

    @staticmethod
    async def get_dashboard(
        db: AsyncSession,
        contract_id: UUID,
    ) -> ContractDashboard | None:

        query = await db.execute(

            select(
                ContractDashboard,
            )

            .where(
                ContractDashboard.contract_id == contract_id,
            )

        )

        return query.scalar_one_or_none()

    @staticmethod
    async def delete_dashboard(
        db: AsyncSession,
        item: ContractDashboard,
    ) -> None:

        await db.delete(item)

    # ==========================================================
    # Join
    # ==========================================================

    @staticmethod
    async def get_contract(
        db: AsyncSession,
        contract_id: UUID,
    ):

        query = await db.execute(

            select(
                ContractRaw,
                ContractDashboard,
            )

            .join(
                ContractDashboard,
                ContractDashboard.contract_id
                == ContractRaw.id,
            )

            .where(
                ContractRaw.id == contract_id,
            )

        )

        return query.first()

    @staticmethod
    async def get_contracts(
        db: AsyncSession,
    ):

        query = await db.execute(

            select(
                ContractRaw,
                ContractDashboard,
            )

            .join(
                ContractDashboard,
                ContractDashboard.contract_id
                == ContractRaw.id,
            )

            .order_by(
                ContractRaw.created_at.desc(),
            )

        )

        return query.all()
    
    
    @staticmethod
    async def get_contract_summaries(
        db: AsyncSession,
    ):

        query = await db.execute(

            select(

                ContractRaw.id,

                ContractDashboard.summary,

            )

            .join(

                ContractDashboard,

                ContractDashboard.contract_id
                == ContractRaw.id,

            )

            .order_by(

                ContractRaw.created_at.desc(),

            )

        )

        results = []

        for row in query.all():

            summary = row.summary

            if len(summary) > 200:

                summary = summary[:200] + "..."

            results.append(

                {

                    "id": str(row.id),

                    "summary": summary,

                }

            )

        return results
    
    @staticmethod
    async def get_extracted_content(
        db: AsyncSession,
        contract_id: UUID,
    ) -> str | None:

        query = await db.execute(

            select(

                ContractRaw.extracted_content,

            )

            .where(

                ContractRaw.id == contract_id,

            )

        )

        return query.scalar_one_or_none()
    
    
    
    @staticmethod
    async def get_all_summaries(
        db: AsyncSession,
    ) -> list[str]:

        query = await db.execute(

            select(
                ContractDashboard.summary,
            )

            .order_by(
                ContractDashboard.created_at.desc(),
            )

        )

        return list(
            query.scalars().all()
        )
    
    @staticmethod
    async def get_contracts(
        db: AsyncSession,
    ):

        query = await db.execute(

            select(

                ContractRaw,
                ContractDashboard,

            )

            .join(

                ContractDashboard,

                ContractDashboard.contract_id
                == ContractRaw.id,

            )

            .order_by(

                ContractRaw.created_at.desc(),

            )

        )

        return query.all()
    
    @staticmethod
    async def get_contract(
        db: AsyncSession,
        contract_id: UUID,
    ):

        query = await db.execute(

            select(

                ContractRaw,
                ContractDashboard,

            )

            .join(

                ContractDashboard,

                ContractDashboard.contract_id
                == ContractRaw.id,

            )

            .where(

                ContractRaw.id == contract_id,

            )

        )

        return query.first()