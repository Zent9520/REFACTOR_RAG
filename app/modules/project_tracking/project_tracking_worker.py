import asyncio

from backend.app.core.database import (
    AsyncSessionLocal,
)

from backend.app.modules.project_tracking.services.project_tracking_sync_service import (
    ProjectTrackingSyncService,
)


class ProjectTrackingWorker:

    @staticmethod
    async def run():

        while True:

            print("=" * 100)
            print("PROJECT TRACKING WORKER START")
            print("=" * 100)

            db = AsyncSessionLocal()

            try:

                await (
                    ProjectTrackingSyncService
                    .sync_all(
                        db=db,
                    )
                )

            except Exception as ex:

                print(ex)

                await db.rollback()

            finally:

                await db.close()

            print("=" * 100)
            print("PROJECT TRACKING WORKER SLEEP 30 MINUTES")
            print("=" * 100)

            await asyncio.sleep(
                30 * 60,
            )