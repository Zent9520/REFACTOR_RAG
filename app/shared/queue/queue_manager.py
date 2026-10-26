from app.shared.queue.local_queue import (
    LocalQueue,
)


class QueueManager:

    def __init__(
        self,
    ):
        self._queues = {}

    def get_queue(
        self,
        queue_name: str,
    ) -> LocalQueue:

        if (
            queue_name
            not in self._queues
        ):

            self._queues[
                queue_name
            ] = LocalQueue()

        return (
            self._queues[
                queue_name
            ]
        )


queue_manager = (
    QueueManager()
)