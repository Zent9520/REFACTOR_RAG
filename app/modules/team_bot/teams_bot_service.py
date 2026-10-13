from botbuilder.core import (

    ActivityHandler,

    TurnContext

)

from backend.app.modules.chat.services.rag_service import (
    RagService
)


class TeamsBotService(

    ActivityHandler

):


    async def on_message_activity(

        self,

        turn_context:
        TurnContext

    ):


        question = (

            turn_context
            .activity
            .text
        )


        rag = (

            RagService()

        )


        answer = await (

            rag.ask(

                question=

                question,


                chunks=[]

            )

        )


        await (

            turn_context

            .send_activity(

                answer
            )

        )