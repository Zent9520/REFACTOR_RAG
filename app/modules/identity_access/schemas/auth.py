from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from backend.app.modules.identity_access.schemas.microsoft_profile import MicrosoftGroup


class LoginUserResponse(BaseModel):

    id: UUID

    email: str

    display_name: str

    avatar_url: str | None

    is_active: bool

    tenant_id: UUID

    microsoft_object_id: UUID

    user_principal_name: str

    groups: list[MicrosoftGroup]

    created_at: datetime

    updated_at: datetime


class LoginResponse(BaseModel):

    access_token: str

    token_type: str = "Bearer"

    expires_in: int

    user: LoginUserResponse
