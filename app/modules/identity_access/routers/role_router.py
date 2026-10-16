from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db
from backend.app.modules.identity_access.schemas.role_schema import (
    RoleCreate,
    RoleResponse
)
from backend.app.modules.identity_access.repositories.role_repository import (
    RoleRepository
)

router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)


@router.post(
    "/",
    response_model=RoleResponse
)
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db)
):
    return await RoleRepository.create(
        db,
        payload.name,
        payload.description
    )


@router.get(
    "",
    
    response_model=list[RoleResponse]
)
async def get_roles(
    db: AsyncSession = Depends(get_db)
):
    return await RoleRepository.get_all(db)