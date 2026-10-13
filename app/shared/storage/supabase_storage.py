from pathlib import Path
from uuid import uuid4

from supabase import create_client

from app.core.settings import settings

import tempfile


class SupabaseStorage:

    BUCKET = "documents"

    _client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY,
    )

    @classmethod
    async def upload_cv(
        cls,
        file_bytes: bytes,
        file_name: str,
        content_type: str,
    ) -> str:

        extension = Path(file_name).suffix.lower()

        storage_path = (
            f"cv/{uuid4()}{extension}"
        )

        cls._client.storage.from_(
            cls.BUCKET
        ).upload(
            path=storage_path,
            file=file_bytes,
            file_options={
                "content-type": content_type,
                "upsert": "false",
            },
        )

        return storage_path

    @classmethod
    async def download(
        cls,
        file_path: str,
    ) -> bytes:

        return cls._client.storage.from_(
            cls.BUCKET
        ).download(
            file_path
        )

    @classmethod
    async def delete(
        cls,
        file_path: str,
    ) -> None:

        cls._client.storage.from_(
            cls.BUCKET
        ).remove(
            [file_path]
        )
        
    @classmethod
    async def download_to_temp_file(
        cls,
        file_path: str,
    ) -> str:

        data = await cls.download(
            file_path
        )

        suffix = Path(
            file_path
        ).suffix

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:

            temp_file.write(
                data
            )

            return temp_file.name