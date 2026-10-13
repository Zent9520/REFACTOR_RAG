from backend.app.modules.knowledge_graph.repositories.entity_context_repository import (
    EntityContextRepository
)

from backend.app.modules.knowledge_graph.repositories.entity_relationship_repository import (
    EntityRelationshipRepository
)

from backend.app.shared.llm.openai_embedding_service import (
    OpenAIEmbeddingService
)


class GraphRetrievalService:

    @staticmethod
    async def retrieve(

        db,

        question: str

    ):

        embedding_service = (
            OpenAIEmbeddingService()
        )

        question_embedding = await (

            embedding_service
            .embed(
                question
            )
        )

        contexts = await (

            EntityContextRepository
            .search_similar(

                db=db,

                embedding=
                question_embedding,

                top_k=10
            )
        )

        relationships = await (

            EntityRelationshipRepository
            .search_similar(

                db=db,

                embedding=
                question_embedding,

                top_k=10
            )
        )

        chunk_ids = set()

        #
        # Context Chunks
        #
        for context in contexts:

            chunk_ids.add(
                context.chunk_id
            )

        #
        # Relationship Chunks
        #
        for relationship in relationships:

            chunk_ids.add(
                relationship.chunk_id
            )

        return list(
            chunk_ids
        )