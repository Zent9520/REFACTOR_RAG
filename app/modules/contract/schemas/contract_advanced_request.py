from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ContractLegalCheck(BaseModel):
    contract_text: str = Field(min_length=1)
    metadata_seeds: dict[str, list[str]]


class ContractLegalReviewRequest(BaseModel):
    model_id: UUID
    output_extract: str

    @field_validator("output_extract")
    @classmethod
    def validate_output_extract(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("output_extract must not be empty.")

        return value


class LegalChatRequest(BaseModel):
    model_id: UUID
    question: str
    extracted_contract: str

    @field_validator("question", "extracted_contract")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Value must not be empty.")

        return value
