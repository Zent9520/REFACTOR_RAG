import httpx

from backend.app.shared.llm.base_llm import (
    BaseLLM
)
from app.core.settings import settings

class OllamaService(BaseLLM):

    def __init__(
        self,
        model: str | None = None
    ):
        self.model = (
            model
            or settings.OLLAMA_MODEL
        )

    async def generate(
        self,
        prompt: str
    ) -> str:

        async with httpx.AsyncClient() as client:

            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            
        

        data = response.json()

        return data["response"].strip()