from uuid import UUID

from sqlalchemy import (
    select,
    update,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.modules.configuration.models.workspace import (
    Workspace,
)

from backend.app.modules.configuration.models.ai_model import (
    AIModel,
)

from backend.app.modules.configuration.models.workspace_model_config import (
    WorkspaceModelConfig,
)

from backend.app.modules.configuration.models.workspace_rag_config import (
    WorkspaceRagConfig,
)

from backend.app.modules.configuration.models.master_config import (
    MasterConfig,
)

from backend.app.modules.configuration.models.embedding_model import (
    EmbeddingModel,
)


class WorkspaceConfigRepository:

    @staticmethod
    async def get_workspace_configuration(
        db: AsyncSession,
        workspace_id: UUID,
    ):

        query = await db.execute(

            select(

                Workspace,

                WorkspaceModelConfig,

                AIModel,

                WorkspaceRagConfig,

                MasterConfig,

                EmbeddingModel,

            )

            .join(

                WorkspaceModelConfig,

                WorkspaceModelConfig.workspace_id
                == Workspace.id,

            )

            .join(

                AIModel,

                AIModel.id
                == WorkspaceModelConfig.model_id,

            )

            .join(

                WorkspaceRagConfig,

                WorkspaceRagConfig.workspace_id
                == Workspace.id,

            )

            .join(

                MasterConfig,

                MasterConfig.id
                == WorkspaceRagConfig.master_config_id,

            )

            .join(

                EmbeddingModel,

                EmbeddingModel.id
                == MasterConfig.embedding_model_id,

            )

            .where(

                Workspace.id
                == workspace_id,

            )

        )

        return query.first()
    
    
    @staticmethod
    async def update_model_config(
        db: AsyncSession,
        workspace_id: UUID,
        temperature: float,
        max_tokens: int,
    ):

        await db.execute(

            update(
                WorkspaceModelConfig,
            )

            .where(

                WorkspaceModelConfig.workspace_id
                == workspace_id,

            )

            .values(

                temperature=temperature,

                max_tokens=max_tokens,

            )

        )
        
    @staticmethod
    async def update_rag_config(
        db: AsyncSession,
        workspace_id: UUID,
        top_k: int,
    ):

        await db.execute(

            update(
                WorkspaceRagConfig,
            )

            .where(

                WorkspaceRagConfig.workspace_id
                == workspace_id,

            )

            .values(

                top_k=top_k,

            )

        )
        
    @staticmethod
    async def get_top_k_by_workspace_code(
        db: AsyncSession,
        workspace_code: str,
    ) -> int | None:

        query = await db.execute(

            select(
                WorkspaceRagConfig.top_k,
            )

            .join(

                Workspace,

                Workspace.id
                == WorkspaceRagConfig.workspace_id,

            )

            .where(

                Workspace.code
                == workspace_code,

            )

        )

        return query.scalar_one_or_none()
    
    
    
    
    @staticmethod
    async def get_model_config_by_workspace_code(
        db: AsyncSession,
        workspace_code: str,
    ) -> WorkspaceModelConfig | None:

        query = await db.execute(

            select(

                WorkspaceModelConfig,

            )

            .join(

                Workspace,

                Workspace.id
                == WorkspaceModelConfig.workspace_id,

            )

            .where(

                Workspace.code
                == workspace_code,

            )

        )

        return query.scalar_one_or_none()
                
            
            