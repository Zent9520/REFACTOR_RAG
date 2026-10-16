from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from backend.app.core.database import (
    get_db,
)

from backend.app.modules.company.meeting.services.meeting_service import (
    MeetingService,
)
from backend.app.modules.company.meeting.schemas.analyze_meeting_request import (
    AnalyzeMeetingRequest,
)
from backend.app.modules.company.meeting.services.meeting_analysis_service import (
    MeetingAnalysisService,
)


router = APIRouter(
    prefix="/meeting",
    tags=["Meeting"],
)


@router.post("/analyze")
async def analyze_meeting(
    request: AnalyzeMeetingRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await MeetingAnalysisService.analyze(
            db=db,
            transcript=request.transcript,
            model_id=request.model_id,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.get("")
async def get_meetings(
    db: AsyncSession = Depends(
        get_db
    ),
):

    return await (
        MeetingService
        .get_all(
            db=db,
        )
    )


@router.get("/{id}")
async def get_meeting(
    id: UUID,
    db: AsyncSession = Depends(
        get_db
    ),
):

    result = await (
        MeetingService
        .get_by_id(
            db=db,
            id=id,
        )
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Meeting not found.",
        )

    return result
