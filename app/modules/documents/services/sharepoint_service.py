import httpx

from app.core.settings import (
    settings
)


class SharePointService:

    LIST_ID = (
        "62207fd2-91ee-4784-9d3a-688adf632a4a"
    )

    @staticmethod
    async def _get_access_token():

        async with httpx.AsyncClient() as client:

            token_response = await client.post(
                f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/oauth2/v2.0/token",
                data={
                    "client_id":
                    settings.AZURE_CLIENT_ID,

                    "client_secret":
                    settings.AZURE_CLIENT_SECRET,

                    "scope":
                    "https://graph.microsoft.com/.default",

                    "grant_type":
                    "client_credentials"
                }
            )

            token_data = (
                token_response.json()
            )

            print(
                "token_status =",
                token_response.status_code
            )

            print(
                token_data
            )

            return (
                token_data.get(
                    "access_token"
                )
            )
            
    @staticmethod
    async def get_list_item_id(
        site_id: str,
        drive_id: str,
        drive_item_id: str,
    ):

        access_token = await (
            SharePointService
            ._get_access_token()
        )

        async with httpx.AsyncClient() as client:

            url = (

                f"https://graph.microsoft.com/v1.0"

                f"/sites/{site_id}"

                f"/drives/{drive_id}"

                f"/items/{drive_item_id}"

                f"/listItem"

            )

            response = await client.get(

                url,

                headers={
                    "Authorization":
                    f"Bearer {access_token}"
                }

            )

            print(
                "list_item_status =",
                response.status_code
            )

            print(
                "list_item_body =",
                response.text
            )

            data = response.json()

            return data.get("id")
    @staticmethod
    async def upload_file(
        department: str,
        file_name: str,
        file_content: bytes
    ):

        access_token = await (
            SharePointService
            ._get_access_token()
        )

        async with httpx.AsyncClient() as client:

            upload_url = (
                f"https://graph.microsoft.com/v1.0"
                f"/sites/{settings.SHAREPOINT_SITE_ID}"
                f"/drives/{settings.SHAREPOINT_DRIVE_ID}"
                f"/root:/{department}/{file_name}:/content"
            )

            print(
                "upload_url =",
                upload_url
            )

            response = await client.put(
                upload_url,
                headers={
                    "Authorization":
                    f"Bearer {access_token}",

                    "Content-Type":
                    "application/octet-stream"
                },
                content=file_content
            )

            print(
                "upload_status =",
                response.status_code
            )

            print(
                "upload_body =",
                response.text
            )

            return (
                response.json()
            )

    @staticmethod
    async def update_metadata(
        site_id: str,
       
        item_id: str,
        department: str,
        owner_role: str,
        security_level: str,
        document_type: str,
        workspace_code: str
    ):

        access_token = await (
            SharePointService
            ._get_access_token()
        )
        
        document_library = await SharePointService.get_document_library(
        site_id
        )

        list_id = document_library["id"]

        async with httpx.AsyncClient() as client:

            metadata_url = (

                f"https://graph.microsoft.com/v1.0"

                f"/sites/{site_id}"

                f"/lists/{list_id}"

                f"/items/{item_id}"

                f"/fields"

            )

            payload = {

                "Ph_x00f2_ngban":
                department,

                "Vaitr_x00f2_s_x1edf_h_x1eef_ut_x1ead_ptin":
                owner_role,

                "L_x1edb_pb_x1ea3_om_x1ead_t":
                security_level,

                "Lo_x1ea1_it_x00e0_ili_x1ec7_u":
                document_type,
                "Workspace":
                workspace_code,

            }

            print("metadata_url =", metadata_url)
            print("payload =", payload)

            response = await client.patch(

                metadata_url,

                headers={
                    "Authorization":
                    f"Bearer {access_token}",

                    "Content-Type":
                    "application/json"
                },

                json=payload

            )

            print("metadata_status =", response.status_code)
            print("metadata_body =", response.text)

            return response.json()
    @staticmethod
    async def _get_headers():

            access_token = await (
                SharePointService
                ._get_access_token()
            )

            return {
                "Authorization":
                f"Bearer {access_token}"
            }
    @staticmethod
    async def get_sites():

        headers = await SharePointService._get_headers()

        async with httpx.AsyncClient() as client:

            response = await client.get(
                "https://graph.microsoft.com/v1.0/sites?search=*",
                headers=headers,
            )

            data = response.json()

            return [
                {
                    "id": site["id"],
                    "name": site["displayName"],
                    "web_url": site["webUrl"],
                }
                for site in data.get("value", [])
            ]
            
    @staticmethod
    async def get_lists(
        site_id: str,
    ):

        headers = await (
            SharePointService
            ._get_headers()
        )

        timeout = httpx.Timeout(
            connect=30.0,
            read=120.0,
            write=120.0,
            pool=120.0,
        )

        async with httpx.AsyncClient(
            timeout=timeout,
        ) as client:

            response = await client.get(

                f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists?$select=id,displayName",

                headers=headers,

            )

            print(
                "lists_status =",
                response.status_code,
            )

            print(
                "lists_body =",
                response.text,
            )

            return (
                response.json()
            )
            
    @staticmethod
    async def get_rag_configuration(
        site_id: str,
        list_id: str,
    ):

        headers = await (
            SharePointService
            ._get_headers()
        )

        async with httpx.AsyncClient() as client:

            response = await client.get(

                f"https://graph.microsoft.com/v1.0"
                f"/sites/{site_id}"
                f"/lists/{list_id}"
                f"/items"
                f"?expand=fields",

                headers=headers

            )

            print(
                "config_status =",
                response.status_code
            )

            print(
                response.text
            )

            return response.json()
    @staticmethod
    async def get_drives(
        site_id: str,
    ):

        headers = await (
            SharePointService
            ._get_headers()
        )

        async with httpx.AsyncClient() as client:

            response = await client.get(

                f"https://graph.microsoft.com/v1.0"
                f"/sites/{site_id}"
                f"/drives",

                headers=headers

            )

            return response.json()
    @staticmethod
    async def get_root_folders(
        drive_id: str,
    ):

        headers = await SharePointService._get_headers()

        async with httpx.AsyncClient() as client:

            response = await client.get(
                f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children",
                headers=headers,
            )

            data = response.json()

            return [
                {
                    "id": item["id"],
                    "name": item["name"],
                }
                for item in data.get("value", [])
                if "folder" in item
            ]
    @staticmethod
    async def find_configuration_list(
        site_id: str,
    ):

        lists = await SharePointService.get_lists(
            site_id=site_id,
        )

        print("=" * 100)
        print("site_id =", site_id)
        print("lists =", lists)

        if "value" not in lists:
            return None

        for item in lists["value"]:

            if item["displayName"] == "RAG Configuration":
                return item

        return None
    
    @staticmethod
    async def get_upload_options():

        sites = await SharePointService.get_sites()

        result = []

        for site in sites:

            configuration_list = await SharePointService.find_configuration_list(
                site_id=site["id"],
            )

            if configuration_list is None:
                continue

            configuration = await SharePointService.get_rag_configuration(
                site_id=site["id"],
                list_id=configuration_list["id"],
            )

            items = configuration.get("value", [])

            if not items:
                continue

            fields = items[0]["fields"]

            if not fields.get("EnableRAG", False):
                continue

            drives = await SharePointService.get_drives(
                site_id=site["id"],
            )

            libraries = []

            for drive in drives.get("value", []):

                folders = await SharePointService.get_root_folders(
                    drive_id=drive["id"],
                )

                libraries.append(
                    {
                        "id": drive["id"],
                        "name": drive["name"],
                        "folders": folders,
                    }
                )

            result.append(
                {
                    "id": site["id"],
                    "name": site["name"],
                    "libraries": libraries,
                }
            )

        return result
    
    @staticmethod
    async def upload_file_sharepoint(
        site_id: str,
        drive_id: str,
        folder_id: str | None,
        file_name: str,
        file_content: bytes,
    ):
        access_token = await SharePointService._get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/octet-stream",
        }

        if folder_id:

            upload_url = (
                f"https://graph.microsoft.com/v1.0"
                f"/drives/{drive_id}"
                f"/items/{folder_id}:/{file_name}:/content"
            )

        else:

            upload_url = (
                f"https://graph.microsoft.com/v1.0"
                f"/sites/{site_id}"
                f"/drives/{drive_id}"
                f"/root:/{file_name}:/content"
            )

        print("upload_url =", upload_url)

        async with httpx.AsyncClient() as client:

            response = await client.put(
                upload_url,
                headers=headers,
                content=file_content,
            )

        print("upload_status =", response.status_code)
        print("upload_body =", response.text)

        return response.json()
    
    @staticmethod
    async def get_document_library(
        site_id: str,
    ):
        lists = await SharePointService.get_lists(site_id)

        for item in lists["value"]:

            if item["displayName"].lower() in [
                "tài liệu",
                "documents",
                "shared documents",
            ]:

                return item

        raise Exception("Document library not found")
    
    @staticmethod
    async def get_delta(
        delta_link: str,
    ):

        access_token = await (
            SharePointService
            ._get_access_token()
        )

        async with httpx.AsyncClient() as client:

            response = await client.get(

                delta_link,

                headers={
                    "Authorization":
                    f"Bearer {access_token}"
                }

            )

            print(
                "delta_status =",
                response.status_code
            )

            print(
                "delta_body =",
                response.text
            )

            return (
                response.json()
            )
            
    # @staticmethod
    # async def get_first_delta(
    #     drive_id: str,
    # ):

    #     headers = await (
    #         SharePointService
    #         ._get_headers()
    #     )

    #     async with httpx.AsyncClient() as client:

    #         response = await client.get(

    #             f"https://graph.microsoft.com/v1.0"
    #             f"/drives/{drive_id}"
    #             f"/root/delta",

    #             headers=headers,

    #         )

    #         print(
    #             "first_delta_status =",
    #             response.status_code,
    #         )

    #         print(
    #             "first_delta_body =",
    #             response.text,
    #         )

    #         return (
    #             response.json()
    #         )
  
    @staticmethod
    async def get_first_delta(
        drive_id: str,
    ):

        access_token = await (
            SharePointService
            ._get_access_token()
        )

        async with httpx.AsyncClient(timeout=60.0) as client:

            response = await client.get(

                f"https://graph.microsoft.com/v1.0"
                f"/drives/{drive_id}"
                f"/root/delta",

                headers={
                    "Authorization":
                    f"Bearer {access_token}"
                }

            )

            print(
                "delta_status =",
                response.status_code
            )

            print(
                "delta_body =",
                response.text
            )

            return (
                response.json()
            )
            
    @staticmethod
    async def get_folders(
        drive_id: str,
        parent_id: str | None = None,
    ):

        headers = await (
            SharePointService
            ._get_headers()
        )

        if parent_id:

            url = (
                f"https://graph.microsoft.com/v1.0"
                f"/drives/{drive_id}"
                f"/items/{parent_id}"
                f"/children"
            )

        else:

            url = (
                f"https://graph.microsoft.com/v1.0"
                f"/drives/{drive_id}"
                f"/root/children"
            )

        async with httpx.AsyncClient() as client:

            response = await client.get(
                url,
                headers=headers,
            )

        data = response.json()

        folders = []

        for item in data.get("value", []):

            if "folder" not in item:
                continue

            children = await (
                SharePointService
                .get_folders(
                    drive_id=drive_id,
                    parent_id=item["id"],
                )
            )

            folders.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "children": children,
                }
            )

        return folders
    
    @staticmethod
    async def get_upload_folder_tree():

        sites = await (
            SharePointService
            .get_sites()
        )

        result = []

        for site in sites:

            configuration = await (
                SharePointService
                .find_configuration_list(
                    site_id=site["id"],
                )
            )

            if configuration is None:
                continue

            rag = await (
                SharePointService
                .get_rag_configuration(
                    site_id=site["id"],
                    list_id=configuration["id"],
                )
            )

            items = rag.get("value", [])

            if not items:
                continue

            if not items[0]["fields"].get(
                "EnableRAG",
                False,
            ):
                continue

            drives = await (
                SharePointService
                .get_drives(
                    site_id=site["id"],
                )
            )

            libraries = []

            for drive in drives.get("value", []):

                libraries.append(
                    {
                        "id": drive["id"],
                        "name": drive["name"],
                        "folders": await (
                            SharePointService
                            .get_folders(
                                drive["id"],
                            )
                        ),
                    }
                )

            result.append(
                {
                    "id": site["id"],
                    "name": site["name"],
                    "libraries": libraries,
                }
            )

        return result
                            
                