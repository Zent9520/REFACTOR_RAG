from uuid import UUID

from pydantic import BaseModel


class ContractChatRequest(
    BaseModel,
):

    question: str

    model_id: UUID
    
    contract_id: UUID