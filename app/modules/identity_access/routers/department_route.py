from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import (
    get_db,
)

from backend.app.modules.identity_access.schemas.department import (
    DepartmentResponse,
)

from backend.app.modules.identity_access.services.department_service import (
    DepartmentService,
)


router = APIRouter(

    prefix="/departments",

    tags=["Departments"],

)


@router.get(
    "",
    response_model=list[DepartmentResponse],
)
async def get_departments(

    db: AsyncSession = Depends(get_db),

):

    return await DepartmentService.get_all(
        db,
    )