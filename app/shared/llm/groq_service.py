from groq import Groq

from backend.app.core.settings import (
    settings
)

from backend.app.shared.llm.base_llm import (
    BaseLLM
)


class GroqService(
    BaseLLM
):

    def __init__(self):

        self.client = Groq(

            api_key=
            settings.GROQ_API_KEY
        )

    async def generate(

        self,

        prompt: str

    ) -> str:

        response = (

            self.client
            .chat
            .completions
            .create(

                model=
                "llama-3.3-70b-versatile",

                messages=[
                    {
                        "role":
                        "user",

                        "content":
                        prompt
                    }
                ]
            )
        )

        return (

            response
            .choices[0]
            .message
            .content
        )