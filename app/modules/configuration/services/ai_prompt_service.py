from datetime import datetime
from datetime import timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.not_found_exception import (
    NotFoundException,
)

from backend.app.modules.configuration.models.ai_prompt import (
    AIPrompt,
)

from backend.app.modules.configuration.repositories.ai_prompt_repository import (
    AIPromptRepository,
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


class AIPromptService:

    @staticmethod
    async def get_all(
        db: AsyncSession,
    ):
        return await AIPromptRepository.get_all(
            db=db,
        )

    @staticmethod
    async def get_paged(
        db: AsyncSession,
        request: GetAIPromptPagedRequest,
    ):
        items, total = await AIPromptRepository.get_paged(
            db=db,
            page=request.page,
            page_size=request.page_size,
        )

        return {
            "items": items,
            "total": total,
            "page": request.page,
            "page_size": request.page_size,
        }

    @staticmethod
    async def create(
        db: AsyncSession,
        request: CreateAIPromptRequest,
    ):
        now = datetime.now(
            timezone.utc,
        )

        prompt = AIPrompt(
            code=request.code,
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            user_prompt=request.user_prompt,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        await AIPromptRepository.create(
            db=db,
            prompt=prompt,
        )

        await db.commit()

        await db.refresh(
            prompt,
        )

        return prompt

    @staticmethod
    async def update(
        db: AsyncSession,
        id: UUID,
        request: UpdateAIPromptRequest,
    ):
        prompt = await AIPromptRepository.get_by_id(
            db=db,
            id=id,
        )

        if prompt is None:
            raise NotFoundException(
                "Prompt not found.",
            )

        prompt.code = request.code
        prompt.name = request.name
        prompt.description = request.description
        prompt.system_prompt = request.system_prompt
        prompt.user_prompt = request.user_prompt
        prompt.updated_at = datetime.now(
            timezone.utc,
        )

        await AIPromptRepository.update(
            db=db,
            prompt=prompt,
        )

        await db.commit()

        await db.refresh(
            prompt,
        )

        return prompt

    @staticmethod
    async def delete(
        db: AsyncSession,
        id: UUID,
    ):
        prompt = await AIPromptRepository.get_by_id(
            db=db,
            id=id,
        )

        if prompt is None:
            raise NotFoundException(
                "Prompt not found.",
            )

        prompt.is_active = False
        prompt.updated_at = datetime.now(
            timezone.utc,
        )

        await AIPromptRepository.update(
            db=db,
            prompt=prompt,
        )

        await db.commit()