import httpx

from app.services.sharepoint.azure_project_tracking_service import (
    AzureProjectTrackingService,
)

from app.services.sharepoint.sharepoint_service import (
    SharePointService,
)


class ProjectTrackingReaderService:

    @staticmethod
    async def load_project(
        project_code: str,
    ):

        print("=" * 100)
        print("LOAD PROJECT")
        print("PROJECT =", project_code)
        print("=" * 100)

        #
        # Lấy danh sách project + metadata
        #

        projects = await (
            AzureProjectTrackingService
            .get_projects()
        )

        project = next(

            (
                item
                for item in projects
                if item["project_code"] == project_code
            ),

            None,

        )

        if project is None:

            raise Exception(
                f"Project '{project_code}' not found."
            )

        print("FILES =", len(project["files"]))

        headers = await (
            SharePointService
            ._get_headers()
        )

        result = {

            "project_code": project_code,

            "files": []

        }

        async with httpx.AsyncClient() as client:

            for file in project["files"]:

                print("-" * 80)
                print("FILE =", file["file_name"])
                print("TYPE =", file["data_type"])
                print("DRIVE =", file["drive_id"])
                print("ITEM =", file["item_id"])

                #
                # Sheet List
                #

                response = await client.get(

                    f"https://graph.microsoft.com/v1.0"
                    f"/drives/{file['drive_id']}"
                    f"/items/{file['item_id']}"
                    f"/workbook/worksheets",

                    headers=headers,

                )

                response.raise_for_status()

                worksheets = response.json().get(
                    "value",
                    [],
                )

                workbook = {

                    "file_name": file["file_name"],

                    "data_type": file["data_type"],

                    "worksheets": []

                }

                print(
                    "TOTAL SHEETS =",
                    len(worksheets),
                )

                #
                # Read every worksheet
                #

                for sheet in worksheets:

                    sheet_name = sheet["name"]

                    print("READ SHEET =", sheet_name)

                    range_response = await client.get(

                        f"https://graph.microsoft.com/v1.0"
                        f"/drives/{file['drive_id']}"
                        f"/items/{file['item_id']}"
                        f"/workbook/worksheets('{sheet_name}')"
                        f"/usedRange",

                        headers=headers,

                    )

                    range_response.raise_for_status()

                    values = (
                        range_response.json()
                        .get("values", [])
                    )

                    print(
                        "ROWS =",
                        len(values),
                    )

                    workbook[
                        "worksheets"
                    ].append(

                        {

                            "sheet_name":
                            sheet_name,

                            "values":
                            values,

                        }

                    )

                result[
                    "files"
                ].append(
                    workbook
                )

        print("=" * 100)
        print("PROJECT LOADED")
        print(result)
        print("=" * 100)

        parsed = (
            ProjectTrackingReaderService
            ._build_project_response(
                result["files"],
            )
        )

        parsed["project_code"] = project_code

        print("=" * 100)
        print(parsed)
        print("=" * 100)

        return parsed
    
    
    @staticmethod
    def _convert_rows(values: list):

        if not values:
            return []

        headers = values[0]

        rows = []

        for value in values[1:]:

            item = {}

            for index, header in enumerate(headers):

                if index >= len(value):
                    continue

                #
                # Bỏ cột rỗng
                #

                if value[index] in ("", None):
                    continue

                item[header] = value[index]

            rows.append(item)

        return rows

    @staticmethod
    def _build_project_response(workbooks: list):

        response = {}

        for workbook in workbooks:

            for worksheet in workbook["worksheets"]:

                sheet = worksheet["sheet_name"]

                rows = ProjectTrackingReaderService._convert_rows(
                    worksheet["values"]
                )

                #
                # Project chỉ có 1 record
                #

                if sheet == "Project":

                    response["project"] = (
                        rows[0]
                        if rows
                        else {}
                    )

                #
                # Các sheet còn lại
                #

                elif sheet == "Tasks":

                    response["tasks"] = rows

                elif sheet == "Members":

                    response["members"] = rows

                elif sheet == "Risks":

                    response["risks"] = rows

                else:

                    response[
                        sheet.lower()
                    ] = rows

        return response