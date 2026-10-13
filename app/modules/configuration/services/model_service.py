from uuid import uuid4
from datetime import datetime
from datetime import timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.configuration.models.ai_model import (
    AIModel,
)

from uuid import UUID

from backend.app.modules.configuration.repositories.ai_model_repository import (
    AIModelRepository,
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

from app.core.bad_request_exception import (
    BadRequestException,
)

from app.core.not_found_exception import (
    NotFoundException,
)


class ModelsService:

    @staticmethod
    async def get_all(
        db: AsyncSession,
    ):
        return await AIModelRepository.get_all(
            db=db,
        )

    @staticmethod
    async def get_paged(
        db: AsyncSession,
        request: GetAIModelPagedRequest,
    ):
        return await AIModelRepository.get_paged(
            db=db,
            request=request,
        )

    @staticmethod
    async def create(
        db: AsyncSession,
        request: CreateAIModelRequest,
    ):
        existed = await AIModelRepository.get_by_code(
            db=db,
            code=request.code,
        )

        if existed:
            raise BadRequestException(
                "Model code already exists.",
            )

        model = AIModel(
            id=uuid4(),
            code=request.code,
            provider=request.provider,
            model_name=request.model_name,
            display_name=request.display_name,
            is_default=request.is_default,
            is_active=True,
            created_at=datetime.now(
                timezone.utc,
            ),
        )

        await AIModelRepository.create(
            db=db,
            model=model,
        )

        await db.commit()
        await db.refresh(model)

        return model

    @staticmethod
    async def update(
        db: AsyncSession,
        id,
        request: UpdateAIModelRequest,
    ):
        model = await AIModelRepository.get_by_id(
            db=db,
            id=id,
        )

        if model is None:
            raise NotFoundException(
                "Model not found.",
            )

        existed = await AIModelRepository.get_by_code(
            db=db,
            code=request.code,
        )

        if existed and existed.id != id:
            raise BadRequestException(
                "Model code already exists.",
            )

        model.code = request.code
        model.provider = request.provider
        model.model_name = request.model_name
        model.display_name = request.display_name
        model.is_default = request.is_default

        await AIModelRepository.update(
            db=db,
            model=model,
        )

        await db.commit()
        await db.refresh(model)

        return model

    @staticmethod
    async def update_active(
        db: AsyncSession,
        id,
        request: UpdateAIModelActiveRequest,
    ):
        model = await AIModelRepository.get_by_id(
            db=db,
            id=id,
        )

        if model is None:
            raise NotFoundException(
                "Model not found.",
            )

        model.is_active = request.is_active

        await AIModelRepository.update(
            db=db,
            model=model,
        )

        await db.commit()
        await db.refresh(model)

        return model
    
    @staticmethod
    async def delete(
            db: AsyncSession,
            id: UUID,
        ):
            model = await AIModelRepository.get_by_id(
                db=db,
                id=id,
            )
    
            if model is None:
                raise NotFoundException(
                    "model not found.",
                )
    
            model.is_active = False
            model.updated_at = datetime.now(
                timezone.utc,
            )
    
            await AIModelRepository.update(
                db=db,
                model=model,
            )
    
            await db.commit()