import httpx

from app.core.settings import settings

from app.services.sharepoint.sharepoint_service import (
    SharePointService,
)


class AzureProjectTrackingService:

    @staticmethod
    async def get_projects():

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
                == settings.PROJECT_TRACKING_SITE_NAME
            ),

            None,

        )

        if site is None:

            raise Exception(
                "Project Tracking Site not found."
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
                == settings.PROJECT_TRACKING_LIBRARY_NAME
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

        files = response.json().get(
            "value",
            [],
        )

        project_map = {}

        # =====================================
        # Read Metadata
        # =====================================

        async with httpx.AsyncClient() as client:

            for file in files:

                if not file["name"].lower().endswith(
                    ".xlsx"
                ):
                    continue

                item_id = file["id"]

                metadata_response = await client.get(

                    f"https://graph.microsoft.com/v1.0"
                    f"/sites/{site_id}"
                    f"/drives/{drive_id}"
                    f"/items/{item_id}"
                    f"/listItem/fields",

                    headers=headers,

                )

                metadata = (
                    metadata_response.json()
                )

                project_code = metadata.get(
                    "Code_project"
                )

                data_type = metadata.get(
                    "Data_type"
                )

                enable_ai = metadata.get(
                    "Enable_AI"
                )

            

                if not project_code:
                    continue

                #
                # Skip nếu Disable AI
                #

                if (
                    enable_ai is not None
                    and str(enable_ai).lower()
                    != "true"
                ):
                    continue

                if project_code not in project_map:

                    project_map[
                        project_code
                    ] = {

                        "project_code":
                        project_code,

                        "files": []

                    }

                project_map[
                    project_code
                ]["files"].append(

                    {

                        "file_name":
                        file["name"],

                        "data_type":
                        data_type,

                        "site_id":
                        site_id,

                        "drive_id":
                        drive_id,

                        "item_id":
                        item_id,

                        "last_modified":
                        file.get(
                            "lastModifiedDateTime"
                        ),

                    }

                )

        return list(
            project_map.values()
        )