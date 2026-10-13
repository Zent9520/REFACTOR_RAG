from google import genai

from openai import AsyncOpenAI

from groq import AsyncGroq

from app.core.settings import settings


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
    async def rewrite(
        history: str,
        question: str
    ) -> str:

        prompt = (
            QueryRewriteService.PROMPT
            .format(
                history=history,
                question=question
            )
        )

        #
        # GEMINI
        #

        try:

            client = genai.Client(
                api_key=
                settings.GEMINI_API_KEY
            )

            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )

            return response.text.strip()

        except Exception as e:

            print(
                "Gemini failed",
                str(e)
            )

        #
        # OPENAI
        #

        try:

            client = AsyncOpenAI(
                api_key=
                settings.OPENAI_API_KEY
            )

            response = await (
                client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
            )

            return (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

        except Exception as e:

            print(
                "OpenAI failed",
                str(e)
            )

        #
        # GROQ
        #

        try:

            client = AsyncGroq(
                api_key=
                settings.GROQ_API_KEY
            )

            response = await (
                client.chat.completions.create(
                    model=
                    "llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
            )

            return (
                response
                .choices[0]
                .message
                .content
                .strip()
            )

        except Exception as e:

            print(
                "Groq failed",
                str(e)
            )

        return question