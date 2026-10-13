import asyncio
from typing import Generic
from typing import TypeVar


T = TypeVar("T")


class LocalQueue(
    Generic[T],
):

    def __init__(
        self,
        max_size: int = 0,
    ):
        self._queue = (
            asyncio.Queue(
                maxsize=max_size,
            )
        )

    async def enqueue(
        self,
        item: T,
    ) -> None:

        await (
            self._queue.put(
                item,
            )
        )

    async def dequeue(
        self,
    ) -> T:

        return await (
            self._queue.get()
        )

    def empty(
        self,
    ) -> bool:

        return (
            self._queue.empty()
        )

    def size(
        self,
    ) -> int:

        return (
            self._queue.qsize()
        )