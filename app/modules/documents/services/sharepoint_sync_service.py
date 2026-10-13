import httpx

from backend.app.core.settings import settings
from backend.app.modules.documents.services.sync_state import SyncState


class SharePointSyncService:

    @staticmethod
    async def trigger():

        SyncState.status = "RUNNING"

        async with httpx.AsyncClient(timeout=300) as client:

            response = await client.post(
                settings.LOGIC_APP_URL,
                json={},
            )

            print(
                "logic_status =",
                response.status_code,
            )

            print(
                "logic_body =",
                response.text,
            )

            return response