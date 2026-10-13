from backend.app.modules.documents.repositories.azure_chunk_repository import (
    AzureChunkRepository
)

from backend.app.modules.knowledge_graph.services.entity_extractor import (
    EntityExtractor
)

from backend.app.modules.knowledge_graph.services.graph_builder_service import (
    GraphBuilderService
)
from backend.app.modules.knowledge_graph.services.entity_embedding_service import (
    EntityEmbeddingService
)
import json



with open(
    "mock_chunks.json",
    "r",
    encoding="utf-8"
) as f:

    mock_results = json.load(f)


class GraphIngestionService:

    @staticmethod
    async def ingest_document(

        db,

        title: str

    ):

        document = (
            AzureChunkRepository
            .load_chunks_by_title(
                title
            )
        )

        if not document:

            raise Exception(
                "Document not found"
            )

        extractor = (
            EntityExtractor()
        )

        chunks = (
            document[
                "chunks"
            ]
        )

        for chunk in chunks:

            result = await (
                extractor.extract(
                    chunk[
                        "content"
                    ]
                )
            )
         

            await (
                GraphBuilderService
                .process_chunk(

                    db=db,

                    chunk_id=
                    chunk[
                        "chunk_id"
                    ],

                    entities=
                    result[
                        "entities"
                    ],

                    relationships=
                    result[
                        "relationships"
                    ]
                )
            )
        await db.commit()
        
        print(
            "BUILD ENTITY EMBEDDINGS..."
        )

        await (

            EntityEmbeddingService
            .build_missing_embeddings(
                db
            )

        )

        print(
            "ENTITY EMBEDDINGS DONE"
        )

        return {

            "title":
            title,

            "chunks":
            len(
                chunks
            )
        }