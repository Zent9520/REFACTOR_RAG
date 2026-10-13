from pydantic import BaseModel

class TagCreate(BaseModel):
    name: str
    description: str | None = None
    sensitivity_level: int = 1
    
class TagResponse(BaseModel):
    id: int
    name: str
    description: str | None
    sensitivity_level: int
    
    model_config = {
        "from_attributes": True
    }
    
    