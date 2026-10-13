import json

from backend.app.shared.llm.llm_factory import (
    LLMFactory
)


class QuestionAnalyzer:

    def __init__(self):

        self.llm = (
         LLMFactory
        .create_openai(
            model=
            "gpt-4.1-mini"
        )
        )

    async def extract_entities(

        self,

        question: str

    ) -> list[str]:

        prompt = f"""
Bạn là model để trích xuất Entity trong câu hỏi người dùng.
Nhiệm vụ của bạn là phân tích, bóc tách câu hỏi sau đó trả về danh sách Entity để so khớp với Entity được nhúng nên cần trả về sát nhất có thể
Hãy trích xuất các entity quan trọng
trong câu hỏi.

Chỉ trả về JSON.

Ví dụ:

{{
    "entities": [
        "Marketing",
        "Trao đổi Kỹ năng Chéo"
    ]
}}

CÂU HỎI:

{question}
"""

        response = await (
            self.llm.generate(
                prompt
            )
        )

        try:

            response = (
                response
                .replace(
                    "```json",
                    ""
                )
                .replace(
                    "```",
                    ""
                )
                .strip()
            )

            parsed = json.loads(
                response
            )
            print("in ra entities model trả về", parsed)

            return parsed.get(
                "entities",
                []
            )

        except Exception:

            return []