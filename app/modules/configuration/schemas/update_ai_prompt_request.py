from pydantic import BaseModel


class UpdateAIPromptRequest(BaseModel):

    code: str

    name: str

    description: str | None = None

    system_prompt: str

    user_prompt: str