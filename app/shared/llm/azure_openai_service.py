import asyncio
import json
from typing import Any, AsyncIterator

from openai import AsyncAzureOpenAI

from backend.app.core.settings import settings
from backend.app.shared.resilience.capacity_manager import capacity_manager
from backend.app.shared.resilience.exceptions import DependencyUnavailableError
from backend.app.shared.resilience.retry_policy import retry_async


class LLMResponseTruncatedError(ValueError):
    pass


def _estimate_tokens(
    messages: list[dict[str, Any]],
    max_completion_tokens: int,
) -> int:
    # A conservative dependency-free estimate for Vietnamese and JSON prompts.
    serialized = json.dumps(messages, ensure_ascii=False, default=str)
    input_tokens = max(1, (len(serialized) + 2) // 3)
    return input_tokens + max(1, int(max_completion_tokens))


class AzureOpenAIService:
    def __init__(self) -> None:
        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT.strip(),
            api_key=settings.AZURE_OPENAI_API_KEY.strip(),
            api_version=settings.AZURE_OPENAI_API_VERSION.strip(),
            max_retries=0,
        )

    async def _create_with_limits(
        self,
        operation,
        operation_name: str,
        estimated_tokens: int,
    ):
        async with capacity_manager.llm_slot(estimated_tokens):
            return await retry_async(
                lambda: asyncio.wait_for(
                    operation(),
                    timeout=settings.AZURE_OPENAI_CHAT_REQUEST_TIMEOUT_SECONDS,
                ),
                operation_name=operation_name,
            )

    async def chat(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.2,
        max_completion_tokens: int = 2000,
    ) -> str:
        max_completion_tokens = max(1, int(max_completion_tokens))
        response = await self._create_with_limits(
            operation=lambda: self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_completion_tokens,
            ),
            operation_name="azure_openai.chat",
            estimated_tokens=_estimate_tokens(messages, max_completion_tokens),
        )
        return response.choices[0].message.content or ""

    async def chat_json(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.2,
        max_completion_tokens: int = 2000,
    ) -> str:
        max_completion_tokens = max(1, int(max_completion_tokens))
        response = await self._create_with_limits(
            operation=lambda: self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_completion_tokens,
                response_format={"type": "json_object"},
            ),
            operation_name="azure_openai.chat_json",
            estimated_tokens=_estimate_tokens(messages, max_completion_tokens),
        )
        choice = response.choices[0]
        if choice.finish_reason == "length":
            raise LLMResponseTruncatedError(
                "LLM JSON response reached the output token limit."
            )
        return choice.message.content or ""

    async def chat_stream(
        self,
        model: str,
        messages: list[dict[str, Any]],
        temperature: float = 0.2,
        max_completion_tokens: int = 2000,
    ) -> AsyncIterator[str]:
        max_completion_tokens = max(1, int(max_completion_tokens))
        estimated_tokens = _estimate_tokens(messages, max_completion_tokens)

        # The slot remains held until streaming finishes or the client disconnects.
        async with capacity_manager.llm_slot(estimated_tokens):
            stream = await retry_async(
                lambda: asyncio.wait_for(
                    self._client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_completion_tokens=max_completion_tokens,
                        stream=True,
                    ),
                    timeout=settings.AZURE_OPENAI_CHAT_REQUEST_TIMEOUT_SECONDS,
                ),
                operation_name="azure_openai.chat_stream.create",
            )

            try:
                async with asyncio.timeout(
                    settings.AZURE_OPENAI_CHAT_REQUEST_TIMEOUT_SECONDS
                ):
                    async for chunk in stream:
                        if not chunk.choices:
                            continue
                        content = chunk.choices[0].delta.content
                        if content:
                            yield content
            except TimeoutError as exc:
                raise DependencyUnavailableError(
                    "Azure OpenAI stream exceeded its timeout."
                ) from exc

    async def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.0,
    ) -> str:
        max_tokens = settings.AZURE_OPENAI_GENERATE_MAX_TOKENS
        messages = [{"role": "user", "content": prompt}]
        response = await self._create_with_limits(
            operation=lambda: self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
            ),
            operation_name="azure_openai.generate",
            estimated_tokens=_estimate_tokens(messages, max_tokens),
        )
        return response.choices[0].message.content or ""
