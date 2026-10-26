import httpx

from urllib.parse import urlencode

from app.core.settings import settings


class GoogleCalendarService:

    GOOGLE_AUTH_URL = (
        "https://accounts.google.com/o/oauth2/v2/auth"
    )

    GOOGLE_TOKEN_URL = (
        "https://oauth2.googleapis.com/token"
    )

    GOOGLE_CALENDAR_EVENTS_URL = (
        "https://www.googleapis.com/calendar/v3/"
        "calendars/primary/events"
    )

    SCOPES = [
        "https://www.googleapis.com/auth/calendar.events.readonly",
    ]


    @staticmethod
    def get_authorization_url() -> str:

        params = {
            "client_id": settings.GOOGLE_CUSTOMER_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(
                GoogleCalendarService.SCOPES
            ),
            "access_type": "offline",
            "prompt": "consent",
        }

        return (
            f"{GoogleCalendarService.GOOGLE_AUTH_URL}"
            f"?{urlencode(params)}"
        )


    @staticmethod
    async def exchange_code(
        code: str,
    ):

        async with httpx.AsyncClient() as client:

            response = await client.post(
                GoogleCalendarService.GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": (
                        settings.GOOGLE_CUSTOMER_ID
                    ),
                    "client_secret": (
                        settings.GOOGLE_CUSTOMER_SECRET
                    ),
                    "redirect_uri": (
                        settings.GOOGLE_REDIRECT_URI
                    ),
                    "grant_type": (
                        "authorization_code"
                    ),
                },
            )

            response.raise_for_status()

            return response.json()


    @staticmethod
    async def get_events(
        access_token: str,
    ):

        async with httpx.AsyncClient() as client:

            response = await client.get(
                GoogleCalendarService
                .GOOGLE_CALENDAR_EVENTS_URL,
                headers={
                    "Authorization": (
                        f"Bearer {access_token}"
                    ),
                },
                params={
                    "maxResults": 50,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                },
            )

            response.raise_for_status()

            data = response.json()

        events = []

        for event in data.get("items", []):

            events.append({
                "id": event.get("id"),

                "title": event.get(
                    "summary"
                ),

                # CÁI CHÚNG TA ĐANG TEST
                "description": event.get(
                    "description"
                ),

                "status": event.get(
                    "status"
                ),

                "html_link": event.get(
                    "htmlLink"
                ),

                "created": event.get(
                    "created"
                ),

                "updated": event.get(
                    "updated"
                ),

                "start": event.get(
                    "start"
                ),

                "end": event.get(
                    "end"
                ),

                "location": event.get(
                    "location"
                ),

                "organizer": event.get(
                    "organizer"
                ),

                "creator": event.get(
                    "creator"
                ),

                "attendees": event.get(
                    "attendees",
                    []
                ),

                "conference_data": event.get(
                    "conferenceData"
                ),

                "hangout_link": event.get(
                    "hangoutLink"
                ),
            })

        return events