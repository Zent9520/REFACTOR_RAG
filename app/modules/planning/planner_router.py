from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.database import (
    get_db,
)

from backend.app.modules.identity_access.dependencies.auth import (
    get_current_user,
)

from backend.app.modules.identity_access.models.user_model import User

from backend.app.modules.planning.planner_service import (
    PlannerService,
)

from fastapi.responses import RedirectResponse

from backend.app.modules.company.meeting.services.google_calendar_service import (
    GoogleCalendarService,
)

router = APIRouter(
    prefix="/planner",
    tags=["Planner"],
)


@router.get("/tasks")
async def get_tasks(
    current_user: User = Depends(
        get_current_user,
    ),
    db: AsyncSession = Depends(
        get_db,
    ),
):

    return await PlannerService.get_my_tasks(
        db=db,
        user_id=str(current_user.id),
    )
    
@router.get("/google-calendar/connect")
async def connect_google_calendar():

    authorization_url = (
        GoogleCalendarService
        .get_authorization_url()
    )

    return RedirectResponse(
        authorization_url
    )


@router.get("/google-calendar/callback")
async def google_calendar_callback(
    code: str,
):

    token_data = await (
        GoogleCalendarService
        .exchange_code(
            code=code,
        )
    )

    access_token = token_data[
        "access_token"
    ]

    events = await (
        GoogleCalendarService
        .get_events(
            access_token=access_token,
        )
    )

    return {
        "token_info": {
            "scope": token_data.get(
                "scope"
            ),
            "token_type": token_data.get(
                "token_type"
            ),
            "expires_in": token_data.get(
                "expires_in"
            ),

            # KHÔNG return access_token
            # KHÔNG return refresh_token
        },

        "total_events": len(events),

        "events": events,
    }