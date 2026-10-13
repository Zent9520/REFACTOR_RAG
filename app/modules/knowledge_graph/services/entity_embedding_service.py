from sqlalchemy import (
    select
)

from backend.app.modules.knowledge_graph.models.entity import (
    Entity
)

from backend.app.shared.llm.openai_embedding_service import (
    OpenAIEmbeddingService
)


class EntityEmbeddingService:

    @staticmethod
    async def build_missing_embeddings(
        db
    ):

        embedding_service = (
            OpenAIEmbeddingService()
        )

        result = await db.execute(

            select(Entity)
            .where(
                Entity.embedding.is_(None)
            )

        )

        entities = (

            result
            .scalars()
            .all()

        )

        print(
            f"Missing Embeddings: {len(entities)}"
        )

        total = 0

        for entity in entities:

            text = f"""
Name:
{entity.name}

Type:
{entity.type or ""}

Description:
{entity.description or ""}
"""

            print(
                f"Embedding: {entity.name}"
            )

            embedding = await (

                embedding_service
                .embed(
                    text
                )

            )

            entity.embedding = (
                embedding
            )

            total += 1

        await db.commit()

        print(
            f"Embedded: {total}"
        )