import asyncio

from backend.app.core.database import (
    AsyncSessionLocal,
)

from backend.app.core.settings import (
    settings,
)

from backend.app.modules.executive_data.services.executive_data_sync_service import (
    ExecutiveDataSyncService,
)


class ExecutiveDataWorker:

    @staticmethod
    async def run():

        while True:

            print("=" * 100)
            print("EXECUTIVE DATA WORKER START")
            print("=" * 100)

            db = AsyncSessionLocal()

            try:

                await (
                    ExecutiveDataSyncService
                    .sync_all(
                        db=db,
                        model_id=settings.EXECUTIVE_DATA_MODEL_ID,
                    )
                )

            except Exception as ex:

                print(ex)

                await db.rollback()

            finally:

                await db.close()

            print("=" * 100)
            print("EXECUTIVE DATA WORKER SLEEP 30 MINUTES")
            print("=" * 100)

            await asyncio.sleep(
                30 * 100,
            )