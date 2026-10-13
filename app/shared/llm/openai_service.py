from openai import AsyncOpenAI

from app.core.settings import (
    settings
)

from backend.app.shared.llm.base_llm import (
    BaseLLM
)


class OpenAIService(
    BaseLLM
):

    def __init__(

        self,

        model: str =
        "gpt-4.1-mini"

    ):

        self.model = (
            model
        )

        self.client = (
            AsyncOpenAI(
                api_key=
                settings
                .OPENAI_API_KEY
            )
        )

    async def generate(

        self,

        prompt: str

    ) -> str:

        response = await (

            self.client
            .chat
            .completions
            .create(

                model=
                self.model,

                messages=[
                    {
                        "role":
                        "user",

                        "content":
                        prompt
                    }
                ],

                temperature=0
            )

        )

        return (
            response
            .choices[0]
            .message
            .content
        )