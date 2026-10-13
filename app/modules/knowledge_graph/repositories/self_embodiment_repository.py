from sqlalchemy import (
    select
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from backend.app.modules.knowledge_graph.models.entity_relationship import (
    EntityRelationship
)


class SelfEmbodimentRepository:

    @staticmethod
    async def exists(

        db: AsyncSession,

        source_entity_id,

        target_entity_id

    ):

        result = await db.execute(

            select(
                EntityRelationship
            )

            .where(

                EntityRelationship
                .source_entity_id
                ==
                source_entity_id
            )

            .where(

                EntityRelationship
                .target_entity_id
                ==
                target_entity_id
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    @staticmethod
    async def create_relationship(

        db: AsyncSession,

        source_entity_id,

        target_entity_id,

        description,

        confidence: float

    ):

        relationship = (

            EntityRelationship(

                source_entity_id=
                source_entity_id,

                target_entity_id=
                target_entity_id,

                chunk_id=
                "self-embodiment",

                description=
                description,

                weight=
                confidence
            )
        )

        db.add(
            relationship
        )

        await db.flush()

        return relationship

    @staticmethod
    async def create_if_not_exists(

        db: AsyncSession,

        source_entity_id,

        target_entity_id,

        description,

        confidence: float

    ):

        exists = await (

            SelfEmbodimentRepository
            .exists(

                db=db,

                source_entity_id=
                source_entity_id,

                target_entity_id=
                target_entity_id
            )
        )

        if exists:

            return exists

        return await (

            SelfEmbodimentRepository
            .create_relationship(

                db=db,

                source_entity_id=
                source_entity_id,

                target_entity_id=
                target_entity_id,

                description=
                description,

                confidence=
                confidence
            )
        )