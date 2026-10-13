from pydantic import BaseModel


class GetAIPromptPagedRequest(BaseModel):

    page: int = 1

    page_size: int = 20