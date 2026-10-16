import asyncio

from backend.app.modules.company.recruitment.reviews.review_worker import review_worker


async def start_queue_consumers() -> None:
    asyncio.create_task(
        review_worker(),
    )