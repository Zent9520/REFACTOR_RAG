from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.knowledge_graph.models.entity import Entity
from sqlalchemy import text

from backend.app.shared.llm.openai_embedding_service import (
    OpenAIEmbeddingService
)

from sqlalchemy import (
    select,
    func
)

from backend.app.modules.knowledge_graph.models.entity_relationship import (
    EntityRelationship
)


class EntityRepository:

    @staticmethod
    async def get_by_name(
        db: AsyncSession,
        name: str
    ):

        result = await db.execute(
            select(Entity)
            .where(Entity.name == name)
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        name: str
    ):

        entity = Entity(
            name=name
        )

        db.add(entity)

        await db.flush()

        return entity

    @staticmethod
    async def get_or_create(

        db,

        name: str,

        type: str | None = None,

        description: str | None = None

    ):

        result = await db.execute(

            select(Entity)

            .where(
                Entity.name.ilike(name)
            )
        )

        entity = result.scalar_one_or_none()

        if entity:

            return entity

        entity = Entity(

            name=name,

            type=type,

            description=description
        )

        db.add(entity)

        await db.flush()

        return entity
    @staticmethod
    async def search_similar(

        db,

        embedding: list[float],

        limit: int = 5

    ):

        vector = (

            "[" +

            ",".join(

                str(x)

                for x in embedding
            )

            + "]"
        )

        result = await db.execute(

            text("""

                SELECT id

                FROM entities

                ORDER BY embedding <=> CAST(

                    :embedding

                    AS vector
                )

                LIMIT :limit

            """),

            {

                "embedding":
                vector,

                "limit":
                limit
            }
        )

        ids = [

            row[0]

            for row in result.fetchall()
        ]

        if not ids:

            return []

        result = await db.execute(

            select(Entity)

            .where(
                Entity.id.in_(ids)
            )
        )

        return (

            result
            .scalars()
            .all()
        )
    @staticmethod
    async def find_similar_entity(

        db,

        entity_name: str

    ):

        embedding_service = (
            OpenAIEmbeddingService()
        )

        embedding = await (

            embedding_service
            .embed(
                entity_name
            )
        )

        result = await (

            EntityRepository
            .search_similar(

                db=db,

                embedding=
                embedding,

                limit=1
            )
        )

        if not result:
            return None

        return result[0]
    
    
    @staticmethod
    async def get_by_ids(

        db,

        ids: list

    ):

        result = await db.execute(

            select(Entity)

            .where(
                Entity.id.in_(ids)
            )
        )

        return (

            result
            .scalars()
            .all()
        )
        
   

    @staticmethod
    async def get_sparse_nodes(

        db,

        degree_threshold: int = 1

    ):

        degree_subquery = (

            select(
                EntityRelationship.source_entity_id.label(
                    "entity_id"
                )
            )

            .union_all(

                select(
                    EntityRelationship.target_entity_id
                )
            )

            .subquery()
        )

        result = await db.execute(

            select(
                Entity
            )

            .outerjoin(

                degree_subquery,

                Entity.id
                ==
                degree_subquery.c.entity_id
            )

            .group_by(
                Entity.id
            )

            .having(

                func.count(
                    degree_subquery.c.entity_id
                )
                <=
                degree_threshold
            )
        )

        return (

            result
            .scalars()
            .all()
        )