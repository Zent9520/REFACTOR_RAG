from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db

from backend.app.modules.configuration.services.workspace_service import (
    WorkspaceSourceConfigService,
)
from backend.app.modules.configuration.schemas.workspace_schema import UpdateAllowOverrideRequest, UpdateSourceModeRequest

router = APIRouter(

    prefix="/configs",

    tags=["Workspace Source Config"],

)

@router.get("")
async def get_all_configs(

    db: AsyncSession = Depends(
        get_db,
    ),

):

    return await (

        WorkspaceSourceConfigService
        .get_all_config(

            db=db,

        )

    )
    
@router.put(
    "/source-mode",
)
async def update_source_mode(

    request: UpdateSourceModeRequest,

    db: AsyncSession = Depends(
        get_db,
    ),

):

    await (

        WorkspaceSourceConfigService
        .update_source_mode(

            db=db,

            workspace_id=request.workspace_id,

            mode_id=request.data_source_mode_id,

        )

    )

    return {

        "message":
        "Update source mode successfully.",

    }


@router.put(
    "/allow-user-override",
)
async def update_allow_user_override(

    request: UpdateAllowOverrideRequest,

    db: AsyncSession = Depends(
        get_db,
    ),

):

    await (

        WorkspaceSourceConfigService
        .update_allow_user_override(

            db=db,

            workspace_id=request.workspace_id,

            allow=request.allow_user_override,

        )

    )

    return {

        "message":
        "Update allow user override successfully.",

    }
    
@router.get(
    "/document-types",
)
async def get_document_types(

    db: AsyncSession = Depends(
        get_db,
    ),

):

    return await (

        WorkspaceSourceConfigService
        .get_all(

            db=db,

        )

    )
    
@router.get(
    "/data-source-modes",
)
async def get_data_source_modes(

    db: AsyncSession = Depends(
        get_db,
    ),

):

    return await (

        WorkspaceSourceConfigService
        .get_all_data_source_modes(

            db=db,

        )

    )
    
    
@router.get("/workspaces")
async def get_list_workspace(
    
    db: AsyncSession = Depends(
        get_db,
    ),
):

    return await (
        WorkspaceSourceConfigService
        .get_list_workspace(
            db=db,
        )
    )   
    


