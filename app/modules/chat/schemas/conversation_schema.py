from pydantic import BaseModel

from uuid import UUID

from datetime import datetime

class ConversationCreate(BaseModel):
    email: str

class ConversationResponse(BaseModel):
     id:UUID

     title:str

     created_at:datetime
     
class Config:
    from_atttributes=True
