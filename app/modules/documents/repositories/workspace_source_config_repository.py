from uuid import UUID

from sqlalchemy import (
    select,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.configuration.models.workspace import (
    Workspace,
)

from backend.app.modules.documents.models.data_source_mode import (
    DataSourceMode,
)
from backend.app.modules.documents.models.document_type import (
    DocumentType,
    )


from backend.app.modules.configuration.models.workspace_source_config import (
    WorkspaceSourceConfig,
)




class WorkspaceSourceConfigRepository:

    # ==========================================================
    # Workspace
    # ==========================================================

    @staticmethod
    async def get_all_workspaces(
        db: AsyncSession,
    ) -> list[Workspace]:

        query = await db.execute(

            select(
                Workspace,
            )
            .order_by(
                Workspace.workspace_name.asc(),
            )

        )

        return list(
            query.scalars().all()
        )

    @staticmethod
    async def get_workspace_by_id(
        db: AsyncSession,
        workspace_id: UUID,
    ) -> Workspace | None:

        query = await db.execute(

            select(
                Workspace,
            )
            .where(
                Workspace.id == workspace_id,
            )

        )

        return query.scalar_one_or_none()

    # ==========================================================
    # Data Source Mode
    # ==========================================================

    @staticmethod
    async def get_all_modes(
        db: AsyncSession,
    ) -> list[DataSourceMode]:

        query = await db.execute(

            select(
                DataSourceMode,
            )
            .order_by(
                DataSourceMode.name.asc(),
            )

        )

        return list(
            query.scalars().all()
        )
    @staticmethod
    async def get_all_document_types(
        db: AsyncSession,
    ) -> list[DocumentType]:

        query = await db.execute(

            select(
                DocumentType,
            )
            .order_by(
                DocumentType.name.asc(),
            )

        )

        return list(
            query.scalars().all()
        )
    @staticmethod
    async def get_mode_by_id(
        db: AsyncSession,
        mode_id: UUID,
    ) -> DataSourceMode | None:

        query = await db.execute(

            select(
                DataSourceMode,
            )
            .where(
                DataSourceMode.id == mode_id,
            )

        )

        return query.scalar_one_or_none()

    # ==========================================================
    # Workspace Config
    # ==========================================================

    @staticmethod
    async def get_all_configs(
        db: AsyncSession,
    ):

        query = await db.execute(

            select(

                WorkspaceSourceConfig,

                Workspace,

                DataSourceMode,

            )

            .join(

                Workspace,

                Workspace.id
                == WorkspaceSourceConfig.workspace_id,

            )

            .join(

                DataSourceMode,

                DataSourceMode.id
                == WorkspaceSourceConfig.data_source_mode_id,

            )

            .order_by(

                Workspace.workspace_name.asc(),

            )

        )

        rows = query.all()

        result = []

        for config, workspace, mode in rows:

            result.append(

                {

                    "workspace_id":
                    workspace.id,

                    "workspace_name":
                    workspace.workspace_name,

                    "data_source_mode": {

                        "id":
                        mode.id,

                        "code":
                        mode.code,

                        "name":
                        mode.name,

                    },

                    "allow_user_override":
                    config.allow_user_override,
                    "is_active":
                    config.is_active,

                }

            )

        return result

    @staticmethod
    async def get_by_workspace_id(
        db: AsyncSession,
        workspace_id: UUID,
    ) -> WorkspaceSourceConfig | None:

        query = await db.execute(

            select(
                WorkspaceSourceConfig,
            )
            .where(
                WorkspaceSourceConfig.workspace_id
                == workspace_id,
            )

        )

        return query.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        item: WorkspaceSourceConfig,
    ) -> None:

        db.add(
            item,
        )

    @staticmethod
    async def update(
        db: AsyncSession,
        item: WorkspaceSourceConfig,
    ) -> None:

        db.add(
            item,
        )
        
    
    @staticmethod
    async def get_data_source_mode_by_document_type(
        db: AsyncSession,
        workspace_code: str,
    ) -> DataSourceMode | None:

        query = await db.execute(

            select(

                DataSourceMode,

            )

            .join(

                WorkspaceSourceConfig,

                WorkspaceSourceConfig.data_source_mode_id
                == DataSourceMode.id,

            )

            .join(

                Workspace,

                Workspace.id
                == WorkspaceSourceConfig.workspace_id,

            )

            .where(

                Workspace.code
                == workspace_code,

            )

        )

        return query.scalar_one_or_none()
    
    
    
    @staticmethod
    async def get_all(
        db: AsyncSession,
    ) -> list[DocumentType]:

        query = await db.execute(

            select(
                DocumentType,
            )
            .order_by(
                DocumentType.name.asc(),
            )

        )

        return list(
            query.scalars().all()
        )
        
    @staticmethod
    async def get_all_data_source_modes(
        db: AsyncSession,
    ) -> list[DataSourceMode]:

        query = await db.execute(

            select(
                DataSourceMode,
            )
            .order_by(
                DataSourceMode.name.asc(),
            )

        )

        return list(
            query.scalars().all()
        )
    
    @staticmethod
    async def get_list_workspace(
        db: AsyncSession,
    ):

        query = await db.execute(

            select(

                Workspace.workspace_name,

                Workspace.code,

            )

            .order_by(

                Workspace.workspace_name.asc(),

            )

        )

        return query.all()
        