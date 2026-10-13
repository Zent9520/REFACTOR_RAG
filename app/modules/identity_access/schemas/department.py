from pydantic import (
    BaseModel,
    ConfigDict,
)


class DepartmentResponse(BaseModel):

    id: int

    name: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )