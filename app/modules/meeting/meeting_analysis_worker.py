# app/workers/meeting_analysis_worker.py

import asyncio

from app.core.database import (
    AsyncSessionLocal,
)

from app.services.azure.meeting_analysis_service import (
    MeetingAnalysisService,
)


CHECK_INTERVAL_SECONDS = (
    60 * 60
)


class MeetingAnalysisWorker:

    @staticmethod
    async def run():

        while True:

            try:

                print(
                    "Starting meeting analysis sync..."
                )

                async with (
                    AsyncSessionLocal()
                    as db
                ):

                    await (
                        MeetingAnalysisService
                        .sync(
                            db=db,
                        )
                    )

                print(
                    "Meeting analysis sync completed."
                )

            except Exception as e:

                print(
                    "MEETING ANALYSIS WORKER ERROR"
                )

                print(e)

            await asyncio.sleep(
                CHECK_INTERVAL_SECONDS
            )