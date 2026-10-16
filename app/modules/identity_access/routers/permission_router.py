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

from backend.app.modules.identity_access.schemas.permission_request import (
    CreatePermissionRequest,
    UpdatePermissionRequest,
)

from backend.app.modules.identity_access.services.permission_service import (
    PermissionService,
)


router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
)



@router.get("/{role}")
async def get_permission(
    role: str,
    db: AsyncSession = Depends(get_db),
):
    return await PermissionService.get_role_access(
        db,
        role,
    )


@router.post("")
async def create_permission(
    request: CreatePermissionRequest,
    db: AsyncSession = Depends(get_db),
):
    return await PermissionService.create(
        db,
        request,
    )


@router.put("/{id}")
async def update_permission(
    id: int,
    request: UpdatePermissionRequest,
    db: AsyncSession = Depends(get_db),
):
    return await PermissionService.update(
        db,
        id,
        request,
    )