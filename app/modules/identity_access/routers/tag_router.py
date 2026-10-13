from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from backend.app.modules.identity_access.schemas.tag_schema import (
    TagCreate, 
    TagResponse
)

from backend.app.modules.identity_access.repositories.tag_repository import (
    TagRepository
)
router = APIRouter(
    prefix="/tags",
    tags=["Tags"]
)
@router.post(
    "/",
    response_model=TagResponse
)
async def create_tag(
    payload: TagCreate,
    db: AsyncSession = Depends(get_db)
):
    return await TagRepository.create(
        db=db,
        name=payload.name,
        description=payload.description,
        sensitivity_level=payload.sensitivity_level,
    )
    
@router.get(
 "/",
response_model=list[TagResponse]
)
async def get_tags(
    db: AsyncSession = Depends(get_db)
):
        return await TagRepository.get_all(db)