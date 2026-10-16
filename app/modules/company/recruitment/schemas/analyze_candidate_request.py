from uuid import UUID

from pydantic import BaseModel


class AnalyzeCandidateRequest(
    BaseModel,
):
    
    model_id: UUID