from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import (
    get_db,
)

from backend.app.modules.configuration.services.model_service import (
    ModelsService,
)

from backend.app.modules.configuration.schemas.create_ai_model_request import (
    CreateAIModelRequest,
)

from backend.app.modules.configuration.schemas.update_ai_model_request import (
    UpdateAIModelRequest,
)

from backend.app.modules.configuration.schemas.get_ai_model_paged_request import (
    GetAIModelPagedRequest,
)

from backend.app.modules.configuration.schemas.update_ai_model_active_request import (
    UpdateAIModelActiveRequest,
)


router = APIRouter(
    prefix="/models",
    tags=["Models"],
)


@router.get("")
async def get_models(
    db: AsyncSession = Depends(get_db),
):
    return await ModelsService.get_all(
        db=db,
    )


@router.post("/paged")
async def get_models_paged(
    request: GetAIModelPagedRequest,
    db: AsyncSession = Depends(get_db),
):
    return await ModelsService.get_paged(
        db=db,
        request=request,
    )


@router.post("")
async def create_model(
    request: CreateAIModelRequest,
    db: AsyncSession = Depends(get_db),
):
    return await ModelsService.create(
        db=db,
        request=request,
    )


@router.put("/{id}")
async def update_model(
    id: UUID,
    request: UpdateAIModelRequest,
    db: AsyncSession = Depends(get_db),
):
    return await ModelsService.update(
        db=db,
        id=id,
        request=request,
    )


@router.put("/{id}/active")
async def update_model_active(
    id: UUID,
    request: UpdateAIModelActiveRequest,
    db: AsyncSession = Depends(get_db),
):
    return await ModelsService.update_active(
        db=db,
        id=id,
        request=request,
    )
    
@router.delete("/{id}")
async def delete_models(
    id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await ModelsService.delete(
        db=db,
        id=id,
    )

    return {
        "message": "Deleted successfully.",
    }