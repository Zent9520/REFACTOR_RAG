from pydantic import BaseModel


class UpdateAIModelActiveRequest(BaseModel):

    is_active: bool