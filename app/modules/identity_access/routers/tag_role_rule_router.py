from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from backend.app.modules.identity_access.schemas.tag_role_rule_schema import (
    TagRoleRuleCreate,
    TagRoleRuleResponse,
)

from backend.app.modules.identity_access.repositories.tag_role_rule_repository import (
    TagRoleRuleRepository
)
router = APIRouter(
    prefix="/tag-role-rules",
    tags=["Tag Role Rules"]
)
@router.post(
    "/",
    response_model = TagRoleRuleResponse
    
)
async def create_rule(
    payload: TagRoleRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    return await TagRoleRuleRepository.create(
        db=db,
        tag_id=payload.tag_id,
        role_id=payload.role_id,

        
    )
@router.get(
    "/",
    response_model=list[TagRoleRuleResponse]
)
async def get_rules(
    db: AsyncSession = Depends(get_db)
):
    return await TagRoleRuleRepository.get_all(db)

