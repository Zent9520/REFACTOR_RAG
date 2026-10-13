from pydantic import BaseModel


class PermissionRequest(BaseModel):

    owner_department_id: int

    viewer_department_id: int

    max_sensitivity_id: int

    position_level_id: int


class CreatePermissionRequest(PermissionRequest):
    pass


class UpdatePermissionRequest(PermissionRequest):
    pass