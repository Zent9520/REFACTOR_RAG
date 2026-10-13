from pydantic import BaseModel


class TagRoleRuleCreate(BaseModel):
    tag_id: int
    role_id: int
class TagRoleRuleResponse(BaseModel):
    id: int
    tag_id: int
    role_id: int
    
    model_config = {
        "from_atttributes": True
    }