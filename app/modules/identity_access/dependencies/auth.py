from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from uuid import UUID

from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from backend.app.modules.identity_access.models.user_model import User

from backend.app.modules.identity_access.repositories.user_repository import (
    UserRepository,
)

from backend.app.modules.identity_access.services.jwt_service import (
    JwtService,
)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security,
    ),
    db: AsyncSession = Depends(
        get_db,
    ),
) -> User:

    payload = JwtService.decode_access_token(
        credentials.credentials,
    )

    user = await UserRepository.get_by_id(
        db=db,
        id=UUID(payload["sub"]),
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    return user