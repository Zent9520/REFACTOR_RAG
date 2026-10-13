# app/services/meeting/microsoft_meeting_service.py

from datetime import datetime, timedelta, timezone
from urllib import response
from urllib.parse import quote

import httpx

from app.core.settings import settings


class MicrosoftMeetingService:

    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    @staticmethod
    def _as_utc(
        value: datetime,
    ) -> datetime:

        if value.tzinfo is None:
            return value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        )

    @staticmethod
    async def get_access_token() -> str:

        token_url = (
            "https://login.microsoftonline.com/"
            f"{settings.AZURE_TENANT_ID}"
            "/oauth2/v2.0/token"
        )

        payload = {
            "client_id": settings.AZURE_CLIENT_ID,
            "client_secret": settings.AZURE_CLIENT_SECRET,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }

        async with httpx.AsyncClient(
            timeout=60
        ) as client:

            response = await client.post(
                token_url,
                data=payload,
            )

            response.raise_for_status()

            data = response.json()

            return data["access_token"]

    @staticmethod
    async def get_calendar_events(
        access_token: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict]:

        start_time = (
            MicrosoftMeetingService
            ._as_utc(
                start_time
            )
        )

        end_time = (
            MicrosoftMeetingService
            ._as_utc(
                end_time
            )
        )

        url = (
            f"{MicrosoftMeetingService.GRAPH_BASE_URL}"
            f"/users/{settings.MEETING_SYNC_USER_ID}"
            "/calendarView"
        )

        params = {
            "startDateTime": start_time.isoformat(),
            "endDateTime": end_time.isoformat(),
            "$top": "100",
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Prefer": 'outlook.timezone="UTC"',
        }

        events = []

        async with httpx.AsyncClient(
            timeout=60
        ) as client:

            while url:

                response = await client.get(
                    url,
                    headers=headers,
                    params=params,
                )

                response.raise_for_status()

                data = response.json()

                events.extend(
                    data.get(
                        "value",
                        [],
                    )
                )

                url = data.get(
                    "@odata.nextLink"
                )

                # nextLink đã chứa query params
                params = None

        return events

    @staticmethod
    async def get_transcripts(
        access_token: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict]:

        user_id = str(
            settings.MEETING_SYNC_USER_ID
        )

        start_utc = (
            MicrosoftMeetingService
            ._as_utc(
                start_time
            )
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        end_utc = (
            MicrosoftMeetingService
            ._as_utc(
                end_time
            )
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        )

        url = (
            f"{MicrosoftMeetingService.GRAPH_BASE_URL}"
            f"/users/{user_id}"
            "/onlineMeetings/getAllTranscripts"
            f"(meetingOrganizerUserId='{user_id}',"
            f"startDateTime={start_utc},"
            f"endDateTime={end_utc})"
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        transcripts = []

        async with httpx.AsyncClient(
            timeout=60
        ) as client:

            while url:

                response = await client.get(
                    url,
                    headers=headers,
                )

                response.raise_for_status()

                data = response.json()

                transcripts.extend(
                    data.get(
                        "value",
                        [],
                    )
                )

                url = data.get(
                    "@odata.nextLink"
                )

        return transcripts

    @staticmethod
    async def get_transcript_content(
        access_token: str,
        meeting_id: str,
        transcript_id: str,
    ) -> str:

        user_id = str(
            settings.MEETING_SYNC_USER_ID
        )

        encoded_meeting_id = quote(
            meeting_id,
            safe="",
        )

        encoded_transcript_id = quote(
            transcript_id,
            safe="",
        )

        url = (
            f"{MicrosoftMeetingService.GRAPH_BASE_URL}"
            f"/users/{user_id}"
            f"/onlineMeetings/{encoded_meeting_id}"
            f"/transcripts/{encoded_transcript_id}"
            "/content"
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "text/vtt",
        }

        async with httpx.AsyncClient(
            timeout=120
        ) as client:

            response = await client.get(
                url,
                headers=headers,
            )

            if response.status_code != 200:
                print(
                    "TRANSCRIPT CONTENT ERROR"
                )
                print(
                    "status =",
                    response.status_code,
                )
                print(
                    "body =",
                    response.text,
                )

            response.raise_for_status()

            return response.text
    @staticmethod
    def get_sync_range():

        now = datetime.now(
            timezone.utc
        )

        start_time = (
            now - timedelta(hours=24)
        )

        return (
            start_time,
            now,
        )
