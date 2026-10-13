from backend.app.modules.knowledge_graph.repositories.entity_repository import (
    EntityRepository
)

from backend.app.modules.knowledge_graph.repositories.entity_context_repository import (
    EntityContextRepository
)

from backend.app.shared.llm.openai_embedding_service import (
    OpenAIEmbeddingService
)

from backend.app.shared.llm.llm_factory import (
    LLMFactory
)

from backend.app.shared.json_helper import (
    JsonHelper
)
from backend.app.modules.knowledge_graph.repositories.self_embodiment_repository import (
    SelfEmbodimentRepository
)
from backend.app.shared.llm.llm_failover_service import (
    LLMFailoverService
)


class GraphCompletionService:

    @staticmethod
    async def build_entity_profile(

        db,

        entity

    ):

        contexts = await (

            EntityContextRepository
            .get_by_entity_id(

                db=db,

                entity_id=
                entity.id,

                limit=5
            )
        )

        context_text = []

        for context in contexts:

            context_text.append(
                context.summary
            )

        return f"""
Name:
{entity.name}

Type:
{entity.type}

Description:
{entity.description}

Contexts:

{chr(10).join(context_text)}
"""

    @staticmethod
    async def judge_relationship(

        profile_a: str,

        profile_b: str

    ):

        

        prompt = f"""
Bạn là chuyên gia xây dựng Knowledge Graph.

Nhiệm vụ:

Xác định xem hai Entity có nên
được nối trực tiếp bằng một
Relationship hay không.

================================

ENTITY A

{profile_a}

================================

ENTITY B

{profile_b}

================================

Trả JSON:

{{
    "should_connect": true,
    "relationship": "...",
    "confidence": 0.95
}}

Rules:

- confidence từ 0 đến 1
- chỉ trả JSON
- nếu không liên quan thì:

{{
    "should_connect": false,
    "relationship": "",
    "confidence": 0.10
}}
"""

        response = await (

            LLMFailoverService
            .generate(
                prompt
            )
        )   
        return (

            JsonHelper
            .parse_llm_json(
                response
            )
        )

    @staticmethod
    async def run(

        db

    ):

        embedding_service = (
            OpenAIEmbeddingService()
        )

        sparse_nodes = await (

            EntityRepository
            .get_sparse_nodes(
                db=db
            )
        )

        print(
            f"Found {len(sparse_nodes)} sparse nodes"
        )
        created_count = 0

        for entity in sparse_nodes:

            print(
                f"\n=== {entity.name} ==="
            )

            #
            # Candidate Search
            #
            candidates = await (

                EntityRepository
                .search_similar(

                    db=db,

                    embedding=
                    entity.embedding,

                    limit=10
                )
            )
            
            print(
                f"\nNODE: {entity.name}"
            )

            print(
                "CANDIDATES:"
            )

            for c in candidates:

                print(
                    f" - {c.name}"
                )

            profile_a = await (

                GraphCompletionService
                .build_entity_profile(

                    db=db,

                    entity=
                    entity
                )
            )

            for candidate in candidates:

                if (
                    candidate.id
                    ==
                    entity.id
                ):
                    continue

                profile_b = await (

                    GraphCompletionService
                    .build_entity_profile(

                        db=db,

                        entity=
                        candidate
                    )
                )
                
                

                result = await (

                    GraphCompletionService
                    .judge_relationship(

                        profile_a=
                        profile_a,

                        profile_b=
                        profile_b
                    )
                )
                
                
                print(
                    f"""
                ================================
                ENTITY:
                {entity.name}

                CANDIDATE:
                {candidate.name}

                RESULT:
                {result}
                ================================
                """
                )
                if not result.get(
                        "should_connect"
                    ):
                    
                        print(
            "SKIP: should_connect = false"
        )

                        continue
                
                confidence = float(

                result.get(
                    "confidence",
                        0
                    )
                )
                
                print(
                    f"CONFIDENCE: {confidence}"
                )

                await (

                SelfEmbodimentRepository
                .create_if_not_exists(

                    db=db,

                    source_entity_id=
                    entity.id,

                    target_entity_id=
                    candidate.id,

                    description=
                    result.get(
                        "relationship"
                    ),

                    confidence=
                    confidence
                )
                
                
                
                
                
                
            )
                created_count += 1
                if created_count % 50 == 0:

                    await db.commit()

                    print(
                        f"""
                        ====================
                        COMMIT
                        TOTAL EDGE:
                        {created_count}
                        ====================
                        """
                    )
                print(
            f"""
        CREATED EDGE

        {entity.name}

        -->

        {candidate.name}

        Confidence:
        {confidence}
        """
        )
        await db.commit()

        print(
            "COMMIT DONE"
        )