from sqlalchemy import (
    or_,
    select
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from backend.app.modules.knowledge_graph.models.entity import (
    Entity
)

from backend.app.modules.knowledge_graph.models.entity_relationship import (
    EntityRelationship
)
from sqlalchemy.orm import aliased


class GraphRepository:
    
    
    
   
    
    
    
    @staticmethod
    async def get_neighbors(

        db,

        entity_id

    ):

        source = aliased(
            Entity
        )

        target = aliased(
            Entity
        )

        result = await db.execute(

            select(

                EntityRelationship,

                source,

                target

            )

            .join(

                source,

                EntityRelationship
                .source_entity_id
                ==
                source.id
            )

            .join(

                target,

                EntityRelationship
                .target_entity_id
                ==
                target.id
            )

            .where(

                or_(

                    EntityRelationship
                    .source_entity_id
                    ==
                    entity_id,

                    EntityRelationship
                    .target_entity_id
                    ==
                    entity_id
                )
            )
        )

        return result.all()

    @staticmethod
    async def get_graph(

        db: AsyncSession

    ):

        #
        # Nodes
        #
        entity_result = await db.execute(

            select(
                Entity
            )
        )

        entities = (
            entity_result
            .scalars()
            .all()
        )

        #
        # Links
        #
        relationship_result = await db.execute(

            select(
                EntityRelationship
            )
        )

        relationships = (

            relationship_result
            .scalars()
            .all()
        )

        nodes = []

        for entity in entities:

            nodes.append({

                "id":
                str(entity.id),

                "name":
                entity.name,

                "type":
                entity.type,

                "description":
                entity.description
            })

        links = []

        for relationship in relationships:

            links.append({

                "source":
                str(
                    relationship
                    .source_entity_id
                ),

                "target":
                str(
                    relationship
                    .target_entity_id
                ),

                "label":
                relationship.description,

                "weight":
                relationship.weight
            })

        return {

            "nodes":
            nodes,

            "links":
            links
        }