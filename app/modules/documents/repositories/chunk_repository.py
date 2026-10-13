import json

from backend.app.modules.documents.repositories.azure_chunk_repository \
import AzureChunkRepository


MOCK_FILE = (
    "mock_chunks.json"
)


class ChunkRepository:


    @staticmethod
    def load_chunks():

        with open(

            MOCK_FILE,

            "r",

            encoding=
            "utf-8"

        ) as f:


            return (
                json.load(f)
            )


    @staticmethod
    def save_chunks(

        chunks

    ):


        with open(

            MOCK_FILE,

            "w",

            encoding=
            "utf-8"

        ) as f:


            json.dump(

                chunks,

                f,

                indent=2,

                ensure_ascii=False

            )


    @staticmethod
    def get_unprocessed_chunks(parent_id: str):

        chunks = (

            AzureChunkRepository
            .load_chunks(parent_id)

        )


        return [

            chunk

            for chunk
            in chunks

            if chunk[
                "processed"
            ]

            is False

        ]


    @staticmethod
    def update_chunk(

        chunk_id,

        updated_chunk

    ):


        chunks = (

            AzureChunkRepository
            .load_chunks()

        )


        for i, chunk in enumerate(
            chunks
        ):


            if (

                chunk["id"]

                ==

                chunk_id

            ):


                chunks[
                    i
                ] = updated_chunk


                break


        ChunkRepository.save_chunks(
            chunks
        )