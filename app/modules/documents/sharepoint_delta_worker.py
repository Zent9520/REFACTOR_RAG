import asyncio

from app.core.database import AsyncSessionLocal
from app.services.delta.delta_service import DeltaService
from app.services.sharepoint.sharepoint_service import SharePointService
from app.services.sharepoint.sharepoint_sync_service import (
    SharePointSyncService,
)

CHECK_INTERVAL_SECONDS = 60 * 60 * 24 * 2  # 2 ngày


async def sharepoint_delta_worker():

    while True:

        try:

            upload_options = await (
                SharePointService
                .get_upload_options()
            )

            changed = False

            async with AsyncSessionLocal() as db:

                for site in upload_options:

                    # print("=" * 80)
                    # print("Checking site:", site["name"])

                    for drive in site["libraries"]:

                        # print("Checking drive:", drive["name"])

                        result = await (
                            DeltaService.check(

                                db=db,

                                site_id=site["id"],

                                drive_id=drive["id"],

                            )
                        )

                        # print("Changed =", result)

                        if result:

                            changed = True
                            break

                    if changed:
                        break

            if changed:

                print("Trigger SharePoint Sync...")

                await (
                    SharePointSyncService
                    .trigger()
                )

        except Exception as e:

            print(
                "SHAREPOINT DELTA WORKER ERROR"
            )

            print(e)

        await asyncio.sleep(
            CHECK_INTERVAL_SECONDS
        )