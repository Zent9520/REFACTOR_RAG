from pydantic import BaseModel


class CreateAIModelRequest(BaseModel):

    code: str

    provider: str

    model_name: str

    display_name: str

    is_default: bool = False