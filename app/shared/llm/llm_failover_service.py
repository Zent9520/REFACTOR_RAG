from backend.app.shared.llm.openai_service import (
    OpenAIService
)

from backend.app.shared.llm.gemini_service import (
    GeminiService
)

from backend.app.shared.llm.groq_service import (
    GroqService
)

from backend.app.shared.llm.openrouter_service import (
    OpenRouterService
)

from backend.app.shared.llm.ollama_service import (
    OllamaService
)


class LLMFailoverService:

    @staticmethod
    async def generate(

        prompt: str

    ):

        providers = [

            GeminiService(),

            GroqService(),

            OpenRouterService(),

            OllamaService(),

            OpenAIService()
        ]

        last_error = None

        for provider in providers:

            try:

                print(
                    f"[LLM] {provider.__class__.__name__}"
                )

                response = await (

                    provider
                    .generate(
                        prompt
                    )
                )

                if (
                    response
                    and
                    str(response).strip()
                ):
                    return response

                raise Exception(
                    "Empty response"
                )

            except Exception as ex:

                last_error = ex

                print(
                    f"[FAIL] {provider.__class__.__name__}"
                )

                print(ex)

        raise last_error