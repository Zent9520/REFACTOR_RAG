from uuid import UUID

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.configuration.repositories.rag_config_repository import (
    WorkspaceConfigRepository,
)


class WorkspaceConfigService:

    @staticmethod
    async def get_workspace_configuration(
        db: AsyncSession,
        workspace_id: UUID,
    ):

        row = await (
            WorkspaceConfigRepository
            .get_workspace_configuration(
                db=db,
                workspace_id=workspace_id,
            )
        )

        if row is None:
            return None

        (
            workspace,
            model_config,
            model,
            rag_config,
            master_config,
            embedding_model,
        ) = row

        return {

            "workspace": {

                "id": workspace.id,

                "name": workspace.workspace_name,

            },

            "model": {

                "provider": model.provider,

                "model": model.model_name,

                "temperature": float(
                    model_config.temperature
                ),

                "max_tokens": model_config.max_tokens,

                "mcp_tool": model_config.mcp_tool,

            },

            "rag": {

                "data_source": rag_config.data_source,

                "chunking": rag_config.chunking_strategy,

                "embedding_model": embedding_model.model_name,

                "top_k": rag_config.top_k,
                "is_active": rag_config.is_active,

            },

        }
        
    @staticmethod
    async def update_model_config(
        db: AsyncSession,
        workspace_id: UUID,
        temperature: float,
        max_tokens: int,
    ):

        await (

            WorkspaceConfigRepository
            .update_model_config(

                db=db,

                workspace_id=workspace_id,

                temperature=temperature,

                max_tokens=max_tokens,

            )

        )

        await db.commit()

        return {

            "message":
            "Model configuration updated successfully."

        }
        
    @staticmethod
    async def update_rag_config(
        db: AsyncSession,
        workspace_id: UUID,
        top_k: int,
    ):

        await (

            WorkspaceConfigRepository
            .update_rag_config(

                db=db,

                workspace_id=workspace_id,

                top_k=top_k,

            )

        )

        await db.commit()

        return {

            "message":
            "RAG configuration updated successfully."

        }