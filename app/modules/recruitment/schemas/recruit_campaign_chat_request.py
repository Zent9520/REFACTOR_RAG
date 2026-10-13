from uuid import UUID

from pydantic import BaseModel


class RecruitmentCampaignChatRequest(
    BaseModel
):

   

    model_id: UUID

    question: str
    
    data_cv: str
    job_descrition:str