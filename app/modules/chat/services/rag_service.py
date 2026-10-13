from uuid import UUID
from typing import AsyncIterator

from backend.app.modules.configuration.enums.prompt_code import (
    PromptCode,
)

from backend.app.modules.configuration.repositories.ai_model_repository import (
    AIModelRepository,
)

from backend.app.modules.configuration.repositories.ai_prompt_repository import (
    AIPromptRepository,
)

from backend.app.shared.llm.azure_openai_service import (
    AzureOpenAIService,
)

from backend.app.modules.chat.services.session_memory_service import (
    SessionMemoryService,
)

from backend.app.modules.configuration.enums.prompt_code import ( PromptCode)
from backend.app.modules.configuration.repositories.rag_config_repository import WorkspaceConfigRepository


class RagService:

    def __init__(self):
        self.llm = AzureOpenAIService()

    async def ask(
        self,
        db,
        conversation_id: UUID,
        question: str,
        chunks: list,
        model_id: UUID,
        mode: PromptCode,
        workspace_code: str,
    ):
        chat_params = await self._build_chat_params(
            db=db,
            conversation_id=conversation_id,
            question=question,
            chunks=chunks,
            model_id=model_id,
            mode=mode,
            workspace_code=workspace_code,
        )
        

        answer = await self.llm.chat(
            model=chat_params["model"],
            messages=chat_params["messages"],
            temperature=chat_params["temperature"],
            max_completion_tokens=chat_params["max_tokens"],
        )

        return answer

    async def ask_stream(
        self,
        db,
        conversation_id: UUID,
        question: str,
        chunks: list,
        model_id: UUID,
        mode: PromptCode,
        workspace_code: str,
    ) -> AsyncIterator[str]:

        chat_params = await self._build_chat_params(
            db=db,
            conversation_id=conversation_id,
            question=question,
            chunks=chunks,
            model_id=model_id,
            mode=mode,
            workspace_code=workspace_code,
        )

        async for token in self.llm.chat_stream(
            model=chat_params["model"],
            messages=chat_params["messages"],
            temperature=chat_params["temperature"],
            max_completion_tokens=chat_params["max_tokens"],
        ):
            yield token

    async def _build_chat_params(
        self,
        db,
        conversation_id: UUID,
        question: str,
        chunks: list,
        model_id: UUID,
        mode: PromptCode,
        workspace_code: str,
    ):

        history = await (
            SessionMemoryService
            .build_context(
                db=db,
                conversation_id=conversation_id,
            )
        )

        if mode not in [
            PromptCode.PUBLIC,
            PromptCode.INTERNAL,
            PromptCode.COMBINE,
        ]:

            raise Exception("Invalid chat mode.")

        prompt = await AIPromptRepository.get_by_code(
            db=db,
            code=mode,
        )

        if prompt is None:
            raise Exception("Prompt not found.")

        model = await (
            AIModelRepository
            .get_by_id(
                db=db,
                id=model_id,
            )
        )

        if model is None:
            raise Exception(
                "AI Model not found."
            )

        contexts = []

        for chunk in chunks:

            contexts.append(
                chunk["content"]
            )

        context = "\n\n".join(contexts)

        system_prompt = (
            prompt.system_prompt
            .replace(
                "{{history}}",
                history or "",
            )
            .replace(
                "{{context}}",
                context,
            )
        )

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ]

        model_config = await (
            WorkspaceConfigRepository
            .get_model_config_by_workspace_code(
                db=db,
                workspace_code=workspace_code,
            )
        )

        return {
            "model": model.model_name,
            "messages": messages,
            "temperature": float(
                model_config.temperature
            ),
            "max_tokens": int(
                model_config.max_tokens
            ),
        }
