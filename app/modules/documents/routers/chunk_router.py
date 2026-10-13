from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from backend.app.core.database import (
    get_db
)

from backend.app.modules.documents.repositories.chunk_repository import (
    ChunkRepository
)

from backend.app.modules.documents.repositories.azure_chunk_repository import (
    AzureChunkRepository
)

from backend.app.modules.documents.services.chunk_processor import (
    ChunkProcessor
)
import json


router = APIRouter(

    prefix="/chunks",

    tags=["Chunks"]

)


# ==========================
# ALL CHUNKS
# ==========================

@router.get("/")
async def get_all_chunks():

    chunks = (

        AzureChunkRepository
        .load_chunks()

    )

    return {

        "total":

        len(chunks),

        "chunks":

        chunks

    }


# ==========================
# UNPROCESSED CHUNKS
# ==========================

@router.get("/unprocessed")
async def get_unprocessed_chunks():

    chunks = (

        ChunkRepository
        .get_unprocessed_chunks()

    )


    result = []


    for chunk in chunks:


        result.append({

            "id":

            chunk.get(
                "id"
            ),


            "processed":

            chunk.get(

                "processed",

                False

            ),


            "department":

            chunk.get(

                "metadata",

                {}

            ).get(

                "department"

            ),


            "security_level":

            chunk.get(

                "metadata",

                {}

            ).get(

                "security_level"

            ),


            "content_preview":

            chunk.get(

                "content",

                ""

            )[:150]

        })


    return {

        "total":

        len(result),

        "chunks":

        result

    }



# ==========================
# PROCESS CHUNKS
# ==========================

@router.post("/process")
async def process_chunks(

    db: AsyncSession =
    Depends(get_db)

):


    open(

        "review_chunks.json",

        "w",

        encoding=
        "utf-8"

    ).close()


    chunks = (

        ChunkRepository
        .get_unprocessed_chunks()

    )


    processed_chunks = []


    for chunk in chunks:


        result = await (

            ChunkProcessor
            .process_chunk(

                db=db,

                chunk=chunk

            )

        )


        processed_chunks.append({

            "id":

            result.get(
                "id"
            ),


            "department":

            result.get(
                "department"
            ),


            "security_level":

            result.get(
                "security_level"
            ),


            "sensitivity":

            result.get(
                "sensitivity"
            ),


            "processed":

            result.get(
                "processed"
            ),


            "content_preview":

            result.get(
                "content_preview",
                ""
            )[:150]

        })


    return {

        "total":

        len(
            processed_chunks
        ),


        "review":

        "review_chunks.json",


        "chunks":

        processed_chunks

    }
    
@router.post(
    "/push-sensitivity"
)

async def push_sensitivity():

    updated = 0


    with open(

        "review_chunks.json",

        encoding=
        "utf-8"

    ) as f:


        for line in f:


            row = json.loads(
                line
            )


            AzureChunkRepository\
            .update_sensitivity(

                chunk_id=

                row["id"],   # id -> chunk_id


                sensitivity=

                int(
                    row[
                        "sensitivity"
                    ]
                )

            )


            updated += 1


    return {

        "updated":

        updated

    }