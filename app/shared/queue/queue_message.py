from dataclasses import dataclass


@dataclass(slots=True)
class QueueMessage:

    queue_name: str

    payload: object