from pydantic import BaseModel


class GraphChatRequest(
    BaseModel
):

    conversation_id: str

    question: str

    role: str | None = None

    email: str | None = None