from backend.app.modules.chat.services.message_service import (
    MessageService
)

from backend.app.modules.chat.services.conversation_summary_service import (
    ConversationSummaryService
)

from backend.app.modules.knowledge_graph.services.graph_traversal_service import (
    GraphTraversalService
)

from backend.app.shared.llm.llm_failover_service import (
    LLMFailoverService
)

from backend.app.shared.llm.openai_service import (
    OpenAIService
)

from backend.app.shared.json_helper import (
    JsonHelper
)


class GraphChatService:

    @staticmethod
    async def ask(

        db,

        conversation_id: str,

        question: str

    ):

        #
        # SAVE USER
        #
        await (

            MessageService
            .create(

                db,

                {

                    "conversation_id":
                    conversation_id,

                    "role":
                    "user",

                    "content":
                    question
                }
            )
        )

        evidence = await (

            GraphTraversalService
            .traverse(

                db=db,

                question=
                question
            )
        )

        context = "\n\n".join(
            evidence
        )

        prompt = f"""
Bạn là trợ lý nội bộ.

Chỉ sử dụng dữ liệu trong CONTEXT.

Trả về JSON:

{{
    "answer": "..."
}}

CONTEXT:

{context}

QUESTION:

{question}
"""

        llm = OpenAIService(
        model="gpt-4.1-mini"
    )

        answer = await (
            llm.generate(
                prompt
            )
        )

        parsed = (

            JsonHelper
            .parse_llm_json(
                answer
            )
        )

        final_answer = (

            parsed.get(
                "answer",
                answer
            )
        )

        #
        # SAVE ASSISTANT
        #
        await (

            MessageService
            .create(

                db,

                {

                    "conversation_id":
                    conversation_id,

                    "role":
                    "assistant",

                    "content":
                    final_answer
                }
            )
        )

        #
        # UPDATE SUMMARY
        #
        await (

            ConversationSummaryService
            .update_summary(

                db=db,

                conversation_id=
                conversation_id
            )
        )

        return {

            "answer":
            final_answer,

            "evidence":
            evidence,

            "conversation_id":
            conversation_id
        }