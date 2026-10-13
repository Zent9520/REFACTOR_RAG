from sqlalchemy import select

from backend.app.core.database import (
    AsyncSessionLocal
)

from backend.app.modules.knowledge_graph.models.entity import (
    Entity
)

from backend.app.shared.llm.openai_embedding_service import (
    OpenAIEmbeddingService
)


async def run():

    embedding_service = (
        OpenAIEmbeddingService()
    )

    async with AsyncSessionLocal() as db:

        result = await db.execute(

            select(Entity)
        )

        entities = (

            result
            .scalars()
            .all()
        )

        total = 0

        for entity in entities:

            #
            # Skip if already embedded
            #
            if entity.embedding is not None:
                continue

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

        print(
            f"Total Entities: {len(entities)}"
        )


if __name__ == "__main__":

    import asyncio

    asyncio.run(
        run()
    )