from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db

from backend.app.modules.identity_access.schemas.policy_schema import (
    ResolveRolesRequest,
    ResolveRolesResponse
)

from backend.app.modules.identity_access.services.policy_engine import (
    PolicyEngine
)

router = APIRouter(
    prefix="/policy",
    tags=["Policy"]
)


@router.post(
    "/resolve",
    response_model=ResolveRolesResponse
)
async def resolve_roles(
    payload: ResolveRolesRequest,
    db: AsyncSession = Depends(get_db)
):
    roles = await PolicyEngine.resolve_roles_from_tags(
        db=db,
        tags=payload.tags
    )

    return {
        "roles": roles
    }