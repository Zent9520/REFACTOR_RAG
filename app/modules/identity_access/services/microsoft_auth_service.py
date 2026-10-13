import asyncio

from app.core.settings import settings
from urllib.parse import urlencode
import httpx
import jwt
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import UUID

from backend.app.schemas.auth.microsoft_profile import (
    MicrosoftGroup,
    MicrosoftProfile,
)


class MicrosoftAuthService:

    AUTHORITY = (
        f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}"
    )

    AUTHORIZE_ENDPOINT = (
        f"{AUTHORITY}/oauth2/v2.0/authorize"
    )

    TOKEN_ENDPOINT = (
        f"{AUTHORITY}/oauth2/v2.0/token"
    )
    @staticmethod
    def get_login_url() -> str:

        query = {
            "client_id": settings.AZURE_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
            "response_mode": "query",
            "scope": (
                "openid "
                "profile "
                "email "
                "offline_access "
                "User.Read "
                "Tasks.Read "
                "Group.Read.All"
            ),
        }

        return (
            f"{MicrosoftAuthService.AUTHORIZE_ENDPOINT}"
            f"?{urlencode(query)}"
        )
        
    @staticmethod
    async def exchange_code(
        code: str,
    ):
        payload = {
            "client_id": settings.AZURE_CLIENT_ID,
            "client_secret": settings.AZURE_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
        }

        async with httpx.AsyncClient() as client:

            response = await client.post(
                MicrosoftAuthService.TOKEN_ENDPOINT,
                data=payload,
            )

            response.raise_for_status()

            token = response.json()

            claims = jwt.decode(
                token["id_token"],
                options={
                    "verify_signature": False,
                },
            )

            token["claims"] = claims

            return token
    

    @staticmethod
    async def get_me(access_token: str):

        async with httpx.AsyncClient() as client:

            response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={
                    "Authorization": f"Bearer {access_token}"
                }
            )

            response.raise_for_status()

            return response.json()
        
    @staticmethod
    async def get_groups(
        access_token: str,
    ) -> list[MicrosoftGroup]:

        url = (
            "https://graph.microsoft.com/v1.0/"
            "me/memberOf/microsoft.graph.group"
            "?$select=id,displayName"
        )
        groups = []

        async with httpx.AsyncClient() as client:

            while url:
                response = await client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {access_token}"
                    },
                )

                response.raise_for_status()
                data = response.json()

                for group in data.get("value", []):
                    group_id = group.get("id")
                    display_name = group.get("displayName")

                    if not group_id or not display_name:
                        continue

                    groups.append(
                        MicrosoftGroup(
                            id=group_id,
                            display_name=display_name,
                        )
                    )

                url = data.get("@odata.nextLink")

        return groups

    @staticmethod
    async def authenticate(
        code: str,
    ) -> MicrosoftProfile:

        token = await MicrosoftAuthService.exchange_code(
            code,
        )

        user, groups = await asyncio.gather(
            MicrosoftAuthService.get_me(token["access_token"]),
            MicrosoftAuthService.get_groups(token["access_token"]),
        )

        claims = token["claims"]

        return MicrosoftProfile(
            tenant_id=UUID(
                claims["tid"],
            ),
            object_id=UUID(
                claims["oid"],
            ),
            email=(
                user["mail"]
                or user["userPrincipalName"]
            ),
            user_principal_name=user[
                "userPrincipalName"
            ],
            display_name=user[
                "displayName"
            ],
            groups=groups,
            refresh_token=token[
                "refresh_token"
            ],
            access_token=token["access_token"],
            access_token_expires_at=(
                datetime.now(
                    timezone.utc,
                )
                + timedelta(
                    seconds=token[
                        "expires_in"
                    ],
                )
            ),
        )
        
    @staticmethod
    async def refresh_access_token(
        refresh_token: str,
    ) -> dict:

        payload = {
            "client_id": settings.AZURE_CLIENT_ID,
            "client_secret": settings.AZURE_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
        }

        async with httpx.AsyncClient() as client:

            response = await client.post(
                MicrosoftAuthService.TOKEN_ENDPOINT,
                data=payload,
            )

            response.raise_for_status()

            return response.json()
