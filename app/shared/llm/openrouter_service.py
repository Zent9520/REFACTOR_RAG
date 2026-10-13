import requests

from backend.app.core.settings import (
    settings
)

from backend.app.shared.llm.base_llm import (
    BaseLLM
)


class OpenRouterService(
    BaseLLM
):

    MODEL_POOL = [

        "deepseek/deepseek-chat",

        "qwen/qwen3-32b",

        "google/gemma-3-27b-it",

        "meta-llama/llama-3.3-70b-instruct"
    ]

    async def generate(

        self,

        prompt: str

    ) -> str:

        for model in (

            self.MODEL_POOL
        ):

            try:

                response = (

                    requests.post(

                        "https://openrouter.ai/api/v1/chat/completions",

                        headers={

                            "Authorization":
                            f"Bearer {settings.OPENROUTER_API_KEY}",

                            "Content-Type":
                            "application/json"
                        },

                        json={

                            "model":
                            model,

                            "messages": [

                                {
                                    "role":
                                    "user",

                                    "content":
                                    prompt
                                }
                            ]
                        },

                        timeout=30
                    )
                )

                response.raise_for_status()

                data = (
                    response.json()
                )

                return (

                    data
                    ["choices"][0]
                    ["message"]
                    ["content"]
                )

            except Exception:

                continue

        raise Exception(
            "OpenRouter failed"
        )