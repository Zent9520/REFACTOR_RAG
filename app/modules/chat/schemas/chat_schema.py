from pydantic import (

    BaseModel

)

from typing import (

    Any

)
from typing import Optional

from uuid import UUID

from backend.app.modules.configuration.enums.prompt_code import ( PromptCode)


class ChatRequest(

    BaseModel

):
    conversation_id: Optional[UUID] = None

    question:str

    microsoft_object_id: str

    group_ids: list[str]


    model_id:str
    
    mode: PromptCode


class ChatResponse(

    BaseModel

):

    answer:str


    email:str


    role:str


    chunks:list[Any]
