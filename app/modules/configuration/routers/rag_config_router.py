from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import (
    get_db,
)

from backend.app.modules.configuration.services.rag_config_service import (
    WorkspaceConfigService,
)
from backend.app.modules.configuration.schemas.rag_config import UpdateWorkspaceModelConfigRequest, UpdateWorkspaceRagConfigRequest

router = APIRouter(
    prefix="/workspace-config",
    tags=["Workspace Config"],
)


@router.get(
    "/{workspace_id}",
)
async def get_workspace_configuration(

    workspace_id: UUID,

    db: AsyncSession = Depends(
        get_db,
    ),

):

    return await (

        WorkspaceConfigService
        .get_workspace_configuration(

            db=db,

            workspace_id=workspace_id,

        )

    )
    
@router.put(
    "/{workspace_id}/model",
)
async def update_workspace_model_config(

    workspace_id: UUID,

    request: UpdateWorkspaceModelConfigRequest,

    db: AsyncSession = Depends(
        get_db,
    ),

):

    return await (

        WorkspaceConfigService
        .update_model_config(

            db=db,

            workspace_id=workspace_id,

            temperature=request.temperature,

            max_tokens=request.max_tokens,

        )

    )
    
@router.put(
    "/{workspace_id}/rag",
)
async def update_workspace_rag_config(

    workspace_id: UUID,

    request: UpdateWorkspaceRagConfigRequest,

    db: AsyncSession = Depends(
        get_db,
    ),

):

    return await (

        WorkspaceConfigService
        .update_rag_config(

            db=db,

            workspace_id=workspace_id,

            top_k=request.top_k,

        )

    )