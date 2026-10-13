from backend.app.shared.queue.queue_message import (
    QueueMessage,
)


class QueueProvider:

    async def publish(
        self,
        message: QueueMessage,
    ) -> None:
        raise NotImplementedError()

    async def consume(
        self,
        queue_name: str,
    ):
        raise NotImplementedError()