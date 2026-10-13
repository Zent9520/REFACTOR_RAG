from backend.app.modules.knowledge_graph.repositories.entity_repository import (
    EntityRepository
)

from backend.app.modules.knowledge_graph.repositories.entity_context_repository import (
    EntityContextRepository
)

from backend.app.modules.knowledge_graph.repositories.graph_repository import (
    GraphRepository
)

from backend.app.shared.llm.openai_embedding_service import (
    OpenAIEmbeddingService
)

from backend.app.modules.knowledge_graph.services.question_analyzer import (
    QuestionAnalyzer
)


class GraphTraversalService:

    @staticmethod
    async def traverse(

        db,

        question: str

    ):

        analyzer = (
            QuestionAnalyzer()
        )

        entity_names = await (

            analyzer
            .extract_entities(
                question
            )
        )

        print(
            "\n=== QUESTION ENTITIES ==="
        )

        print(
            entity_names
        )

        embedding_service = (
            OpenAIEmbeddingService()
        )

        roots = []

        root_ids = set()

        #
        # Find Seed Entities
        # via Entity Context
        #
        for entity_name in entity_names:

            entity_embedding = await (

                embedding_service
                .embed(
                    entity_name
                )
            )

            contexts = await (

                EntityContextRepository
                .search_similar(

                    db=db,

                    embedding=
                    entity_embedding,

                    top_k=5
                )
            )

            print(
                f"\n=== CONTEXTS FOR: {entity_name} ==="
            )

            for context in contexts:

                print(
                    context.summary
                )

            entity_ids = list({

                context.entity_id

                for context in contexts
            })

            if not entity_ids:
                continue

            entities = await (

                EntityRepository
                .get_by_ids(

                    db=db,

                    ids=entity_ids
                )
            )

            for entity in entities:

                if entity.id in root_ids:
                    continue

                root_ids.add(
                    entity.id
                )

                roots.append(
                    entity
                )

        print(
            "\n=== ROOT ENTITIES ==="
        )

        for root in roots:

            print(
                root.name
            )

        evidence = []

        visited = set()

        queue = []

        #
        # Seed Nodes
        #
        for root in roots:

            queue.append(

                (
                    root,
                    0
                )
            )

        #
        # BFS 3 Hops
        #
        while queue:

            node, depth = (
                queue.pop(0)
            )

            if depth > 3:
                continue

            if node.id in visited:
                continue

            visited.add(
                node.id
            )

            evidence.append(

                f"""
Entity:
{node.name}

Type:
{node.type}

Description:
{node.description}
"""
            )

            neighbors = await (

                GraphRepository
                .get_neighbors(

                    db=db,

                    entity_id=
                    node.id
                )
            )

            for relation, source, target in neighbors:

                if source.id == node.id:

                    next_node = target

                else:

                    next_node = source

                evidence.append(

                    f"""
Relationship:

{source.name}

->

{target.name}

Reason:

{relation.description}
"""
                )

                if (

                    next_node.id
                    not in visited

                ):

                    queue.append(

                        (
                            next_node,
                            depth + 1
                        )
                    )

        return evidence