from dataclasses import dataclass

from uuid import UUID


@dataclass(slots=True)
class ReviewTaskMessage:

    task_id: UUID