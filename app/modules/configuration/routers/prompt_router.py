from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.core.database import (
    get_db,
)

from backend.app.modules.configuration.schemas.create_ai_prompt_request import (
    CreateAIPromptRequest,
)

from backend.app.modules.configuration.schemas.update_ai_prompt_request import (
    UpdateAIPromptRequest,
)

from backend.app.modules.configuration.schemas.get_ai_prompt_paged_request import (
    GetAIPromptPagedRequest,
)

from backend.app.modules.configuration.services.ai_prompt_service import (
    AIPromptService,
)

router = APIRouter(
    prefix="/prompts",
    tags=["AI Prompt"],
)


@router.get("")
async def get_prompts(
    db: AsyncSession = Depends(get_db),
):
    return await AIPromptService.get_all(
        db=db,
    )


@router.post("/paged")
async def get_prompts_paged(
    request: GetAIPromptPagedRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AIPromptService.get_paged(
        db=db,
        request=request,
    )


@router.post("")
async def create_prompt(
    request: CreateAIPromptRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AIPromptService.create(
        db=db,
        request=request,
    )


@router.put("/{id}")
async def update_prompt(
    id: UUID,
    request: UpdateAIPromptRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AIPromptService.update(
        db=db,
        id=id,
        request=request,
    )


@router.delete("/{id}")
async def delete_prompt(
    id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await AIPromptService.delete(
        db=db,
        id=id,
    )

    return {
        "message": "Deleted successfully.",
    }