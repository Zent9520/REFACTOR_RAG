from datetime import datetime, timedelta, timezone

import httpx

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.identity_access.repositories.microsoft_account_repository import (
    MicrosoftAccountRepository,
)

from backend.app.modules.identity_access.services.microsoft_auth_service import (
    MicrosoftAuthService,
)
from backend.app.modules.identity_access.models.microsoft_account import MicrosoftAccount


class PlannerService:

    GRAPH_ENDPOINT = (
        "https://graph.microsoft.com/v1.0"
    )

    @staticmethod
    async def get_my_tasks(
        db: AsyncSession,
        user_id: str,
    ):

        account = (
            await MicrosoftAccountRepository.get_by_user_id(
                db=db,
                user_id=user_id,
            )
        )

        if account is None:
            raise Exception(
                "Microsoft account not found."
            )

        token = (
            await MicrosoftAuthService.refresh_access_token(
                account.refresh_token,
            )
        )

        account.refresh_token = token.get(
            "refresh_token",
            account.refresh_token,
        )

        async with httpx.AsyncClient() as client:

            response = await client.get(
                f"{PlannerService.GRAPH_ENDPOINT}/me/planner/tasks",
                headers={
                    "Authorization": (
                        f"Bearer {token['access_token']}"
                    )
                },
            )

            response.raise_for_status()

            return response.json()
        
    @staticmethod
    async def _get_access_token(
        db: AsyncSession,
        account: MicrosoftAccount,
    ) -> str:

        now = datetime.now(timezone.utc)

        if (
            account.access_token
            and account.access_token_expires_at > now
        ):
            return account.access_token

        token = (
            await MicrosoftAuthService.refresh_access_token(
                account.refresh_token,
            )
        )

        account.access_token = token["access_token"]

        account.refresh_token = token.get(
            "refresh_token",
            account.refresh_token,
        )

        account.access_token_expires_at = (
            now
            + timedelta(
                seconds=token["expires_in"],
            )
        )

        account.updated_at = now

        await MicrosoftAccountRepository.update(
            db=db,
            account=account,
        )

        return account.access_token