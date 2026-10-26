import time
from uuid import UUID
from typing import AsyncIterator

from app.core.timing import timed, logger
from app.core.settings import settings

from app.modules.configuration.enums.prompt_code import (
    PromptCode,
)

from app.modules.configuration.chat_config_cache import ChatConfigCache

from app.shared.llm.azure_openai_service import (
    get_shared_chat_service,
)

from app.modules.chat.services.session_memory_service import (
    SessionMemoryService,
)

class RagService:

    def __init__(self):
        self.llm = get_shared_chat_service()

    async def ask(
        self,
        db,
        conversation_id: UUID,
        question: str,
        chunks: list,
        model_id: UUID | str,
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
        model_id: UUID | str,
        mode: PromptCode,
        workspace_code: str,
        history: str | None = None,
        trace_id: str | None = None,
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
                history=history,
            )

        start = time.perf_counter()
        first_token = True

        async for token in self.llm.chat_stream(
            model=chat_params["model"],
            messages=chat_params["messages"],
            temperature=chat_params["temperature"],
            max_completion_tokens=chat_params["max_tokens"],
            trace_id=trace_id,
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
        model_id: UUID | str,
        mode: PromptCode,
        workspace_code: str,
        history: str | None = None,
    ):

        with timed("build_params.TOTAL"):

            if history is None:
                with timed("db.history"):
                    with timed("db.history.connection"):
                        await db.connection()
                    with timed("db.history.query"):
                        history = await SessionMemoryService.build_context(
                            db=db, conversation_id=conversation_id
                        )

            if mode not in [
                PromptCode.PUBLIC,
                PromptCode.INTERNAL,
                PromptCode.COMBINE,
            ]:

                raise Exception("Invalid chat mode.")

            with timed("config.lookup"):
                prompt, model, model_config = await ChatConfigCache.get_chat_settings(
                    mode.value, model_id, workspace_code
                )

            if prompt is None:
                raise Exception("Prompt not found.")

            if model is None:
                raise Exception(
                    "AI Model not found."
                )

            history = (history or "")[-settings.RAG_MAX_HISTORY_CHARS:]
            contexts = []
            context_chars = 0

            for chunk in chunks:
                content = str(chunk.get("content") or "")
                remaining = settings.RAG_MAX_CONTEXT_CHARS - context_chars
                if remaining <= 0:
                    break
                selected = content[:remaining]
                contexts.append(selected)
                context_chars += len(selected)

            context = "\n\n".join(contexts)

            system_prompt = (
                prompt
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

            return {
                "model": model.model_name,
                "messages": messages,
                "temperature": float(
                    model_config.temperature
                ),
                "max_tokens": min(
                    int(model_config.max_tokens),
                    settings.RAG_MAX_OUTPUT_TOKENS,
                ),
            }
