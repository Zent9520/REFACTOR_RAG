from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class RecruitmentCampaignCreate(BaseModel):

    role_id: int

    title: str

    job_description: str


class RecruitmentCampaignResponse(BaseModel):

    id: UUID

    role_id: int

    title: str

    job_description: str

    status: str

    created_at: datetime

    class Config:

        from_attributes = True
        
from uuid import UUID

from pydantic import (
    BaseModel,
)

from datetime import datetime


class RecruitmentCandidateResponse(
    BaseModel
):

    task_id: UUID

    file_name: str

    score: int | float | None = None

    assessment: str | None = None


class RecruitmentCampaignResponse(
    BaseModel
):

    id: UUID

    title: str

    role_id: int

    job_description: str

    status: str

    total_candidates: int

    created_at: datetime

    updated_at: datetime

    candidates: list[
        RecruitmentCandidateResponse
    ]
    
class RecruitmentCampaignCreateResponse(
    BaseModel
):

    id: UUID

    title: str

    role_id: int

    job_description: str

    status: str

    created_at: datetime

    updated_at: datetime


class RecruitmentCandidateDetailResponse(
    BaseModel
):

    task_id: UUID

    campaign_id: UUID

    file_name: str

    score: int | float | None = None

    assessment: str | None = None

    reason: str | None = None

    summary: str | None = None

    strengths: list[str] = []

    weaknesses: list[str] = []

    review_result: dict | None = None