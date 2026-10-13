from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.identity_access.models.role import (
    Role,
)

from backend.app.modules.identity_access.models.department import (
    Department,
)

from backend.app.modules.identity_access.models.position_level import (
    PositionLevel,
)

from backend.app.modules.identity_access.models.sensitivity_level import (
    SensitivityLevel,
)

from backend.app.modules.identity_access.models.department_sensitivity_permission import (
    DepartmentSensitivityPermission,
)


class PermissionRepository:

    @staticmethod
    async def get_role_access(
        db: AsyncSession,
        role_name: str,
    ):

        role_query = await db.execute(
            select(Role).where(
                Role.name == role_name,
            )
        )

        role = role_query.scalar_one_or_none()

        if role is None:
            return []

        result = await db.execute(
            select(
                Department.name,
                SensitivityLevel.priority,
                SensitivityLevel.code,
            )
            .join(
                DepartmentSensitivityPermission,
                Department.id
                == DepartmentSensitivityPermission.owner_department_id,
            )
            .join(
                SensitivityLevel,
                SensitivityLevel.id
                == DepartmentSensitivityPermission.max_sensitivity_id,
            )
            .where(
                DepartmentSensitivityPermission.viewer_department_id
                == role.department_id,
                DepartmentSensitivityPermission.position_level_id
                == role.position_level_id,
            )
        )

        permissions = result.all()

        print("Permission:", permissions)

        return [
            {
                "department": row[0],
                "max_sensitivity": row[1],
                "sensitivity_code": row[2],
            }
            for row in permissions
        ]
        
    @staticmethod
    async def create(
        db: AsyncSession,
        permission: DepartmentSensitivityPermission,
    ) -> DepartmentSensitivityPermission:

        db.add(permission)

        await db.flush()

        await db.refresh(permission)

        return permission

    @staticmethod
    async def update(
        db: AsyncSession,
        permission: DepartmentSensitivityPermission,
    ) -> DepartmentSensitivityPermission:

        db.add(permission)

        await db.flush()

        await db.refresh(permission)

        return permission
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        id: int,
    ) -> DepartmentSensitivityPermission | None:

        result = await db.execute(
            select(
                DepartmentSensitivityPermission
            ).where(
                DepartmentSensitivityPermission.id == id
            )
        )

        return result.scalar_one_or_none()