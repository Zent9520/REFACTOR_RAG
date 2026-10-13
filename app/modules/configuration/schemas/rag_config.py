from pydantic import BaseModel


class UpdateWorkspaceModelConfigRequest(
    BaseModel,
):

    temperature: float

    max_tokens: int


class UpdateWorkspaceRagConfigRequest(
    BaseModel,
):

    top_k: int