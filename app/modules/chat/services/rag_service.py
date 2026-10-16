import time
from uuid import UUID
from typing import AsyncIterator

from backend.app.core.timing import timed, logger

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
        with timed("ask.build_params"):
            chat_params = await self._build_chat_params(
                db=db,
                conversation_id=conversation_id,
                question=question,
                chunks=chunks,
                model_id=model_id,
                mode=mode,
                workspace_code=workspace_code,
            )

        with timed("ask.llm_chat"):
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

        if mode == PromptCode.INTERNAL and not chunks:
            logger.info("[retrieval] No accessible chunks; skipping answer model")
            yield "Không tìm thấy tài liệu nội bộ phù hợp trong phạm vi quyền truy cập của bạn."
            return

        with timed("ask_stream.build_params"):
            chat_params = await self._build_chat_params(
                db=db,
                conversation_id=conversation_id,
                question=question,
                chunks=chunks,
                model_id=model_id,
                mode=mode,
                workspace_code=workspace_code,
            )

        start = time.perf_counter()
        first_token = True

        async for token in self.llm.chat_stream(
            model=chat_params["model"],
            messages=chat_params["messages"],
            temperature=chat_params["temperature"],
            max_completion_tokens=chat_params["max_tokens"],
        ):
            if first_token:
                logger.info(
                    "[timing] ask_stream.llm_first_token: %.2fs",
                    time.perf_counter() - start,
                )
                first_token = False
            yield token

        logger.info(
            "[timing] ask_stream.llm_stream_total: %.2fs",
            time.perf_counter() - start,
        )

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

        with timed("build_params.TOTAL"):

            with timed("db.history"):
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

            with timed("db.prompt"):
                prompt = await AIPromptRepository.get_by_code(
                    db=db,
                    code=mode,
                )

            if prompt is None:
                raise Exception("Prompt not found.")

            with timed("db.model"):
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

            logger.info(
                "[timing] prompt_size: chunks=%d context_chars=%d "
                "history_chars=%d system_prompt_chars=%d",
                len(chunks),
                len(context),
                len(history or ""),
                len(system_prompt),
            )

            with timed("db.model_config"):
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