import httpx

from backend.app.core.settings import settings

from backend.app.modules.documents.services.sharepoint_service import (
    SharePointService,
)


class AzureExecutiveDataService:

    @staticmethod
    async def get_datasets():

        headers = await (
            SharePointService
            ._get_headers()
        )

        # =====================================
        # Find Site
        # =====================================

        sites = await (
            SharePointService
            .get_sites()
        )

        site = next(

            (
                item
                for item in sites
                if item["name"]
                == settings.EXECUTIVE_DATA_SITE_NAME
            ),

            None,

        )

        if site is None:

            raise Exception(
                "Executive Data Site not found."
            )

        site_id = site["id"]

        # =====================================
        # Find Document Library
        # =====================================

        drives = await (
            SharePointService
            .get_drives(
                site_id=site_id,
            )
        )

        drive = next(

            (
                item
                for item in drives["value"]
                if item["name"]
                == settings.EXECUTIVE_DATA_LIBRARY_NAME
            ),

            None,

        )

        if drive is None:

            raise Exception(
                "Document Library not found."
            )

        drive_id = drive["id"]

        # =====================================
        # Get Files
        # =====================================

        async with httpx.AsyncClient() as client:

            response = await client.get(

                f"https://graph.microsoft.com/v1.0"
                f"/drives/{drive_id}"
                f"/root/children",

                headers=headers,

            )

        response.raise_for_status()

        files = response.json().get(
            "value",
            [],
        )

        datasets = []

        # =====================================
        # Build Dataset List
        # =====================================

        for file in files:

            if not file["name"].lower().endswith(
                ".xlsx"
            ):
                continue

            datasets.append(

                {

                    "file_name":
                    file["name"],

                    "site_id":
                    site_id,

                    "drive_id":
                    drive_id,

                    "item_id":
                    file["id"],

                    "last_modified":
                    file.get(
                        "lastModifiedDateTime",
                    ),

                }

            )

        return datasets