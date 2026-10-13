from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.knowledge_graph.models.entity_relationship import (
    EntityRelationship
)

from sqlalchemy import (
    select
)




class EntityRelationshipRepository:

    @staticmethod
    async def exists(

        db: AsyncSession,

        source_entity_id,

        target_entity_id

    ):

        result = await db.execute(

            select(EntityRelationship)

            .where(
                EntityRelationship
                .source_entity_id
                == source_entity_id
            )

            .where(
                EntityRelationship
                .target_entity_id
                == target_entity_id
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    @staticmethod
    async def create(

        db: AsyncSession,

        source_entity_id,

        target_entity_id,

        chunk_id,

        description,

        embedding=None,

        weight: float = 1.0

    ):

        relation = EntityRelationship(

            source_entity_id=
            source_entity_id,

            target_entity_id=
            target_entity_id,

            chunk_id=
            chunk_id,

            description=
            description,

            embedding=
            embedding,

            weight=
            weight
        )

        db.add(
            relation
        )

        await db.flush()

        return relation

    @staticmethod
    async def create_if_not_exists(

        db: AsyncSession,

        source_entity_id,

        target_entity_id,

        chunk_id,

        description,

        embedding=None,

        weight: float = 1.0

    ):

        relation = await (
            EntityRelationshipRepository
            .exists(

                db,

                source_entity_id,

                target_entity_id
            )
        )

        if relation:

            return relation

        return await (

            EntityRelationshipRepository
            .create(

                db=db,

                source_entity_id=
                source_entity_id,

                target_entity_id=
                target_entity_id,

                chunk_id=
                chunk_id,

                description=
                description,

                embedding=
                embedding,

                weight=
                weight
            )
        )
    @staticmethod
    async def search_similar(

        db: AsyncSession,

        embedding: list[float],

        top_k: int = 10

    ):

        result = await db.execute(

            select(
                EntityRelationship
            )

            .order_by(

                EntityRelationship
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
        