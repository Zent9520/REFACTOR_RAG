import httpx

from backend.app.modules.documents.services.sharepoint_service import (
    SharePointService,
)


class ExecutiveDataReaderService:

    @staticmethod
    async def load_dataset(
        dataset: dict,
    ):

        print("=" * 100)
        print("LOAD EXECUTIVE DATA")
        print(dataset["file_name"])
        print("=" * 100)

        headers = await (
            SharePointService
            ._get_headers()
        )

        result = {}

        async with httpx.AsyncClient() as client:

            #
            # Get Worksheets
            #

            response = await client.get(

                f"https://graph.microsoft.com/v1.0"
                f"/drives/{dataset['drive_id']}"
                f"/items/{dataset['item_id']}"
                f"/workbook/worksheets",

                headers=headers,

            )

            response.raise_for_status()

            worksheets = response.json().get(
                "value",
                [],
            )

            print(
                "TOTAL SHEETS =",
                len(worksheets),
            )

            #
            # Read every worksheet
            #

            for sheet in worksheets:

                sheet_name = sheet["name"]

                print(
                    "READ SHEET =",
                    sheet_name,
                )

                range_response = await client.get(

                    f"https://graph.microsoft.com/v1.0"
                    f"/drives/{dataset['drive_id']}"
                    f"/items/{dataset['item_id']}"
                    f"/workbook/worksheets('{sheet_name}')"
                    f"/usedRange",

                    headers=headers,

                )

                range_response.raise_for_status()

                values = (
                    range_response.json()
                    .get(
                        "values",
                        [],
                    )
                )

                print(
                    "ROWS =",
                    len(values),
                )

                result[
                    sheet_name
                ] = (

                    ExecutiveDataReaderService
                    ._convert_rows(
                        values,
                    )

                )

        print("=" * 100)
        print(result)
        print("=" * 100)

        return result

    @staticmethod
    def _convert_rows(
        values: list,
    ):

        if not values:
            return []

        headers = values[0]

        rows = []

        for value in values[1:]:

            item = {}

            for index, header in enumerate(headers):

                if index >= len(value):
                    continue

                if value[index] in (
                    "",
                    None,
                ):
                    continue

                item[
                    header
                ] = value[index]

            rows.append(
                item,
            )

        return rows