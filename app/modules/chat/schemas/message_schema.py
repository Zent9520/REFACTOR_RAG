from pydantic import BaseModel

from uuid import UUID

from datetime import datetime

class MessageCreate(
    BaseModel
):
    conversation_id: UUID
    role: str
    content: str
    
class MessageResponse(BaseModel):
    id:UUID

    conversation_id:UUID

    role:str

    content:str

    created_at:datetime
class Config:
    from_attributes=True
    
    