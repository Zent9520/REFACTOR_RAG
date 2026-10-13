from pydantic import BaseModel


class GetAIModelPagedRequest(BaseModel):

    page: int = 1

    page_size: int = 20

  

    is_active: bool | None = None