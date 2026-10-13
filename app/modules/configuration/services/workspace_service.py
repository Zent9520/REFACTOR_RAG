from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.not_found_exception import (
    NotFoundException,
)

from backend.app.modules.documents.repositories.workspace_source_config_repository import (
    WorkspaceSourceConfigRepository,
)


class WorkspaceSourceConfigService:

    @staticmethod
    async def get_all_config(
        db: AsyncSession,
    ):

        return await (
            WorkspaceSourceConfigRepository
            .get_all_configs(
                db=db,
            )
        )

    @staticmethod
    async def update_source_mode(
        db: AsyncSession,
        workspace_id: UUID,
        mode_id: UUID,
    ):

        config = await (
            WorkspaceSourceConfigRepository
            .get_by_workspace_id(
                db=db,
                workspace_id=workspace_id,
            )
        )

        if config is None:

            raise NotFoundException(
                "Workspace configuration not found."
            )

        mode = await (
            WorkspaceSourceConfigRepository
            .get_mode_by_id(
                db=db,
                mode_id=mode_id,
            )
        )

        if mode is None:

            raise NotFoundException(
                "Data source mode not found."
            )

        config.data_source_mode_id = mode.id

        config.updated_at = datetime.now(
            timezone.utc,
        )

        await (
            WorkspaceSourceConfigRepository
            .update(
                db=db,
                item=config,
            )
        )

        await db.commit()

    @staticmethod
    async def update_allow_user_override(
        db: AsyncSession,
        workspace_id: UUID,
        allow: bool,
    ):

        config = await (
            WorkspaceSourceConfigRepository
            .get_by_workspace_id(
                db=db,
                workspace_id=workspace_id,
            )
        )

        if config is None:

            raise NotFoundException(
                "Workspace configuration not found."
            )

        config.allow_user_override = allow

        config.updated_at = datetime.now(
            timezone.utc,
        )

        await (
            WorkspaceSourceConfigRepository
            .update(
                db=db,
                item=config,
            )
        )

        await db.commit()
        
        
    @staticmethod
    async def get_all(
        db: AsyncSession,
    ):

        document_types = await (

            WorkspaceSourceConfigRepository
            .get_all(
                db=db,
            )

        )

        return [

            {

                "code":
                item.code,

                "name":
                item.name,

            }

            for item in document_types

        ]
        
    
    @staticmethod
    async def get_all_data_source_modes(
        db: AsyncSession,
    ):

        modes = await (

            WorkspaceSourceConfigRepository
            .get_all_data_source_modes(

                db=db,

            )

        )

        return [

            {

                "id":
                item.id,

                "code":
                item.code,

                "name":
                item.name,

            }

            for item in modes

        ]
    
    @staticmethod
    async def get_list_workspace(
        db: AsyncSession,
    ):

        workspaces = await (
            WorkspaceSourceConfigRepository
            .get_list_workspace(
                db=db,
            )
        )

        return [

            {

                "workspace_name":
                workspace.workspace_name,

                "code":
                workspace.code,

            }

            for workspace in workspaces

        ]