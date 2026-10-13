from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import get_db

from backend.app.modules.identity_access.schemas.auth import LoginResponse

from backend.app.modules.identity_access.services.auth_service import AuthService

from backend.app.modules.identity_access.services.microsoft_auth_service import (
    MicrosoftAuthService,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.get("/microsoft/login")
async def microsoft_login():

    return {
        "login_url": MicrosoftAuthService.get_login_url(),
    }


@router.get(
    "/microsoft/callback",
    response_model=LoginResponse,
)
async def microsoft_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
):

    return await AuthService.microsoft_login(
        db=db,
        code=code,
    )
