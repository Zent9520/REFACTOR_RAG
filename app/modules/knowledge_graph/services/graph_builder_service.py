from backend.app.modules.knowledge_graph.repositories.entity_repository import (
    EntityRepository
)

from backend.app.modules.knowledge_graph.repositories.entity_context_repository import (
    EntityContextRepository
)

from backend.app.modules.knowledge_graph.repositories.entity_relationship_repository import (
    EntityRelationshipRepository
)

from backend.app.shared.llm.openai_embedding_service import (
    OpenAIEmbeddingService
)

from backend.app.modules.knowledge_graph.services.embedding_builder import (
    EmbeddingBuilder
)



class GraphBuilderService:

    @staticmethod
    async def process_chunk(

        db,

        chunk_id: str,

        entities: list,

        relationships: list

    ):

        entity_map = {}
        
        embedding_service = (
            OpenAIEmbeddingService()
        )

        #
        # Save Entities
        #
        for item in entities:

            entity = await (
                EntityRepository
                .get_or_create(

                    db=db,

                    name=item["name"],

                    type=item.get(
                        "type"
                    ),

                    description=item.get(
                        "description"
                    )
                )
            )

            key = (
                item["name"]
                .strip()
                .lower()
            )

            entity_map[
                key
            ] = entity

        #
        # Save Contexts
        #
        for item in entities:

            key = (
                item["name"]
                .strip()
                .lower()
            )

            entity = entity_map[
                key
            ]

            entity_text = (

            EmbeddingBuilder
            .build_entity_text(

                name=
                item["name"],

                type=
                item["type"],

                description=
                item["description"]
            )
        )

            entity_embedding = await (

                embedding_service
                .embed(
                    entity_text
                )
            )

            await (

            EntityContextRepository
            .create(

                db=db,

                entity_id=
                entity.id,

                chunk_id=
                chunk_id,

                summary=
                item["description"],

                embedding=
                entity_embedding
            )
        )

        #
        # Save Relationships
        #
        for relation in relationships:

            source = (
                entity_map
                .get(
                    relation[
                        "source"
                    ]
                    .strip()
                    .lower()
                )
            )

            target = (
                entity_map
                .get(
                    relation[
                        "target"
                    ]
                    .strip()
                    .lower()
                )
            )

            if not source:
                continue

            if not target:
                continue

            relationship_text = (

            EmbeddingBuilder
            .build_relationship_text(

                source_name=
                relation["source"],

                target_name=
                relation["target"],

                description=
                relation["description"]
            )
        )

            relationship_embedding = await (

            embedding_service
            .embed(
                relationship_text
            )
        )

            await (

            EntityRelationshipRepository
            .create(

                db=db,

                source_entity_id=
                source.id,

                target_entity_id=
                target.id,

                chunk_id=
                chunk_id,

                description=
                relation["description"],

                embedding=
                relationship_embedding,

                weight=1
            )
        )