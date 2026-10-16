from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ReviewFileResponse(BaseModel):

    task_id: UUID

    file_name: str

    status: str

    review_result: Any | None

    extraction: Any | None = None


class ReviewResponse(BaseModel):

    job_id: UUID

    status: str

    total_files: int

    results: list[ReviewFileResponse]
