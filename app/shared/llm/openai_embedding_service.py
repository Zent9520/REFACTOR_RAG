from openai import AsyncOpenAI

from app.core.settings import (
    settings
)


class OpenAIEmbeddingService:

    def __init__(self):

        self.client = AsyncOpenAI(
            api_key=
            settings.OPENAI_API_KEY
        )

    async def embed(

        self,

        text: str

    ) -> list[float]:

        response = await (
            self.client.embeddings.create(

                model=
                "text-embedding-3-small",

                input=text
            )
        )

        return (
            response
            .data[0]
            .embedding
        )