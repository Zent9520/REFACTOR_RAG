import google.generativeai as genai

from app.core.settings import (
    settings
)

from backend.app.shared.llm.base_llm import (
    BaseLLM
)


class GeminiService(
    BaseLLM
):

    def __init__(self):

        genai.configure(

            api_key=
            settings.GOOGLE_API_KEY
        )

        self.model = (

            genai.GenerativeModel(

                "gemini-2.5-flash"
            )
        )

    async def generate(

        self,

        prompt: str

    ) -> str:

        response = (

            self.model
            .generate_content(
                prompt
            )
        )

        return (
            response.text
        )