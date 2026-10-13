from uuid import UUID

from pydantic import BaseModel


class ExecutiveDataRequest(
    BaseModel,
):
    
    model_id: UUID
    
class ExecutiveDataChatRequest(BaseModel):

    question: str

    model_id: UUID