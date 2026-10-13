from pydantic import BaseModel

class ResolveRolesRequest(BaseModel):
    tags: list[str]
    
class ResolveRolesResponse(
    BaseModel
):
    role: list[str]