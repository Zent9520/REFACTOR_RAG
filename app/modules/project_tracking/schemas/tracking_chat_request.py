from pydantic import BaseModel
from uuid import UUID

class TrackingChatRequest(BaseModel):
    question: str
    model_id: UUID