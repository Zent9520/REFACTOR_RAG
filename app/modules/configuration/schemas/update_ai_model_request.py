from pydantic import BaseModel


class UpdateAIModelRequest(BaseModel):

    code: str

    provider: str

    model_name: str

    display_name: str

    is_default: bool