from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.knowledge_graph.models.entity_context import (
    EntityContext
)
from sqlalchemy import text

from sqlalchemy import (
    select
)




class EntityContextRepository:

    @staticmethod
    async def create(
        db: AsyncSession,

        entity_id: int,

        chunk_id: str,

        summary: str,

        embedding: list[float]
    ):

        context = EntityContext(

            entity_id=entity_id,

            chunk_id=chunk_id,

            summary=summary,

            embedding=embedding
        )

        db.add(context)

        await db.flush()

        return context
    @staticmethod
    async def search_similar(

            db: AsyncSession,

            embedding: list[float],

            top_k: int = 10

        ):

            result = await db.execute(

                select(
                    EntityContext
                )

                .order_by(

                    EntityContext
                    .embedding
                    .cosine_distance(
                        embedding
                    )
                )

                .limit(
                    top_k
                )
            )

            return (
                result
                .scalars()
                .all()
            )
    @staticmethod
    async def search_similar_entity_ids(

        db: AsyncSession,

        embedding: list[float],

        top_k: int = 10

    ):

        contexts = await (

            EntityContextRepository
            .search_similar(

                db=db,

                embedding=embedding,

                top_k=top_k
            )
        )

        return list({

            context.entity_id

            for context in contexts
        })
        
    @staticmethod
    async def get_by_entity_id(

        db,

        entity_id: str,

        limit: int = 5

    ):

        result = await db.execute(

            select(
                EntityContext
            )

            .where(

                EntityContext.entity_id
                ==
                entity_id
            )

            .limit(
                limit
            )
        )

        return (

            result
            .scalars()
            .all()
        )
                    
                