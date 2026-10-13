from pydantic import BaseModel
from uuid import UUID


class UpdateSourceModeRequest(
    BaseModel,
):

    workspace_id: UUID

    data_source_mode_id: UUID
    
class UpdateAllowOverrideRequest(
    BaseModel,
):

    workspace_id: UUID

    allow_user_override: bool