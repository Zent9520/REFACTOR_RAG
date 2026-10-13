from uuid import uuid4
from datetime import (
    datetime,
    timezone,
)

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.ai.user_model import User
from backend.app.models.identity_access.microsoft_account import MicrosoftAccount

from backend.app.repositories.identity.user_repository import UserRepository
from backend.app.repositories.identity.microsoft_account_repository import (
    MicrosoftAccountRepository,
)

from backend.app.schemas.auth.auth import LoginResponse, LoginUserResponse
from backend.app.schemas.auth.microsoft_profile import MicrosoftProfile

from app.services.microsoft.microsoft_auth_service import (
    MicrosoftAuthService,
)

from app.services.jwt.jwt_service import JwtService


class AuthService:

    @staticmethod
    async def microsoft_login(
        db: AsyncSession,
        code: str,
    ) -> LoginResponse:

        profile = await MicrosoftAuthService.authenticate(
            code=code,
        )

        user = await AuthService._find_or_create_user(
            db=db,
            profile=profile,
        )

        await AuthService._sync_microsoft_account(
            db=db,
            user=user,
            profile=profile,
        )

        access_token = JwtService.create_access_token(
            user_id=str(user.id),
            email=user.email,
        )

        return LoginResponse(
            access_token=access_token,
            expires_in=86400,
            user=LoginUserResponse(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
                tenant_id=profile.tenant_id,
                microsoft_object_id=profile.object_id,
                user_principal_name=profile.user_principal_name,
                groups=profile.groups,
                created_at=user.created_at,
                updated_at=user.updated_at,
            ),
        )

    @staticmethod
    async def _find_or_create_user(
        db: AsyncSession,
        profile: MicrosoftProfile,
    ) -> User:

        user = await UserRepository.get_by_email(
            db=db,
            email=profile.email,
        )

        if user is not None:
            return user

        now = datetime.now(timezone.utc)

        user = User(
            id=uuid4(),
            email=profile.email,
            display_name=profile.display_name,
            avatar_url=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        return await UserRepository.create(
            db=db,
            user=user,
        )

    @staticmethod
    async def _sync_microsoft_account(
        db: AsyncSession,
        user: User,
        profile: MicrosoftProfile,
    ) -> None:

        account = (
            await MicrosoftAccountRepository.get_by_object_id(
                db=db,
                object_id=profile.object_id,
            )
        )

        now = datetime.now(timezone.utc)

        if account is None:

            account = MicrosoftAccount(
    id=uuid4(),
    user_id=user.id,
    tenant_id=profile.tenant_id,
    object_id=profile.object_id,
    user_principal_name=profile.user_principal_name,
    access_token=profile.access_token,
    refresh_token=profile.refresh_token,
    access_token_expires_at=profile.access_token_expires_at,
    created_at=now,
    updated_at=now,
)

            await MicrosoftAccountRepository.create(
                db=db,
                account=account,
            )

            return

        account.user_principal_name = profile.user_principal_name
        account.access_token = profile.access_token
        account.refresh_token = profile.refresh_token
        account.access_token_expires_at = (
            profile.access_token_expires_at
        )
        account.updated_at = now

        await MicrosoftAccountRepository.update(
            db=db,
            account=account,
        )
