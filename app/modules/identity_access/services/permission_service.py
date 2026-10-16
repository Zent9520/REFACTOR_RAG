from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.identity_access.models.department_sensitivity_permission import (
    DepartmentSensitivityPermission,
)

from backend.app.modules.identity_access.repositories.permission_repository import (
    PermissionRepository,
)

from backend.app.core.not_found_exception import (
    NotFoundException,
)

from backend.app.modules.identity_access.schemas.permission_request import (
    CreatePermissionRequest, UpdatePermissionRequest
)


class PermissionService:

    @staticmethod
    async def get_role_access(
        db: AsyncSession,
        role_name: str,
    ):
        return await PermissionRepository.get_role_access(
            db,
            role_name,
        )

  

    @staticmethod
    async def create(
        db: AsyncSession,
        request: CreatePermissionRequest,
    ):

        permission = DepartmentSensitivityPermission(
            owner_department_id=request.owner_department_id,
            viewer_department_id=request.viewer_department_id,
            max_sensitivity_id=request.max_sensitivity_id,
            position_level_id=request.position_level_id,
        )

        permission = await PermissionRepository.create(
            db,
            permission,
        )

        await db.commit()

        return permission
    
    
    
   


    @staticmethod
    async def update(
        db: AsyncSession,
        id: int,
        request: UpdatePermissionRequest,
    ):

        permission = await PermissionRepository.get_by_id(
            db,
            id,
        )

        if permission is None:
            raise NotFoundException("Permission not found.")

        permission.owner_department_id = request.owner_department_id
        permission.viewer_department_id = request.viewer_department_id
        permission.max_sensitivity_id = request.max_sensitivity_id
        permission.position_level_id = request.position_level_id

        permission = await PermissionRepository.update(
            db,
            permission,
        )

        await db.commit()

        return permission