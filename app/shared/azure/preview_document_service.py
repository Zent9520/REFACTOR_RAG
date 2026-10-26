import httpx

from app.core.settings import settings


class PreviewDocumentService:

    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    @staticmethod
    async def get_access_token() -> str:
        token_url = (
            f"https://login.microsoftonline.com/"
            f"{settings.AZURE_TENANT_ID}/oauth2/v2.0/token"
        )

        payload = {
            "client_id": settings.AZURE_CLIENT_ID,
            "client_secret": settings.AZURE_CLIENT_SECRET,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=payload,
            )

            response.raise_for_status()

            data = response.json()

        return data["access_token"]

    @staticmethod
    async def get_document_preview_url(
        drive_id: str,
        drive_item_id: str,
    ) -> str:

        access_token = (
            await PreviewDocumentService.get_access_token()
        )

        preview_url = (
            f"{PreviewDocumentService.GRAPH_BASE_URL}"
            f"/drives/{drive_id}"
            f"/items/{drive_item_id}"
            f"/preview"
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                preview_url,
                headers=headers,
                json={},
            )

            response.raise_for_status()

            data = response.json()

        return data["getUrl"]