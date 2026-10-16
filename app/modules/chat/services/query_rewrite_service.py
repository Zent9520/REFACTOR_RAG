import asyncio
import logging

from openai import AsyncAzureOpenAI
from backend.app.core.settings import settings
from backend.app.core.timing import timed

logger = logging.getLogger(__name__)


class QueryRewriteService:
    PROMPT = """
Bạn là bộ máy rewrite câu hỏi cho hệ thống RAG.

Nhiệm vụ:

- Dựa vào lịch sử hội thoại history.
- Nếu câu hỏi hiện tại thiếu ngữ cảnh không rõ ràng thì bổ sung.
- Nếu câu hỏi hiện tại đã đầy đủ thì giữ nguyên.
- Chỉ trả về câu hỏi hoàn chỉnh.
- Không giải thích.

History:
{history}

Question:
{question}
"""

    @staticmethod
    async def rewrite(history: str, question: str) -> str:
        if not history.strip() or not settings.CHAT_REWRITE_DEPLOYMENT.strip():
            return question
        prompt = QueryRewriteService.PROMPT.format(history=history, question=question)
        with timed("retrieval.rewrite"):
            try:
                return await asyncio.wait_for(
                    QueryRewriteService._generate(prompt, question),
                    timeout=settings.CHAT_REWRITE_TIMEOUT_SECONDS,
                )
            except Exception as exc:
                logger.warning("Query rewrite failed (%s); using original question", type(exc).__name__)
                return question

    @staticmethod
    async def _generate(prompt: str, question: str) -> str:
        async with AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT.strip(),
            api_key=settings.AZURE_OPENAI_API_KEY.strip(),
            api_version=settings.AZURE_OPENAI_API_VERSION.strip(),
            timeout=settings.CHAT_REWRITE_TIMEOUT_SECONDS,
            max_retries=0,
        ) as client:
            response = await client.chat.completions.create(
                model=settings.CHAT_REWRITE_DEPLOYMENT,
                messages=[{"role": "user", "content": prompt}],
            )
            return (response.choices[0].message.content or "").strip() or question
