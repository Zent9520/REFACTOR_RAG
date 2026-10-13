from backend.app.shared.queue.queue_manager import (
    queue_manager,
)

from backend.app.shared.queue.queue_message import (
    QueueMessage,
)

from app.shared.queue.queue_provider import (
    QueueProvider,
)


class LocalQueueProvider(
    QueueProvider,
):

    async def publish(
        self,
        message: QueueMessage,
    ) -> None:

        queue = queue_manager.get_queue(
            message.queue_name,
        )

        await queue.enqueue(
            message.payload,
        )

    async def consume(
        self,
        queue_name: str,
    ):
        queue = queue_manager.get_queue(
            queue_name,
        )

        return await queue.dequeue()


queue_provider = LocalQueueProvider()