import asyncio
import json
from time import perf_counter
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.contract.contract_advanced_logging import contract_split_logger
from backend.app.modules.configuration.enums.prompt_code import PromptCode
from backend.app.modules.configuration.repositories.ai_model_repository import AIModelRepository
from backend.app.modules.configuration.repositories.ai_prompt_repository import AIPromptRepository
from backend.app.modules.configuration.repositories.rag_config_repository import (
    WorkspaceConfigRepository,
)
from backend.app.modules.contract.services.legal_chat_retrieval_service import (
    LegalChatRetrievalService,
)
from backend.app.shared.llm.azure_openai_service import AzureOpenAIService


class LegalChatService:
    MAX_RETRIEVAL_SEEDS = 6
    EMPTY_RETRIEVAL_ANSWER = (
        "Không tìm thấy đủ nguồn pháp luật phù hợp trong dữ liệu "
        "hiện tại để trả lời câu hỏi này."
    )
    ALLOWED_METADATA_FIELDS = {
        "doc_type",
        "doc_number",
        "year",
        "issuer",
        "issuer_kind",
        "tier",
        "tier_name",
        "legal_area",
        "section",
        "title",
        "source",
        "issue_date",
        "effective_date",
        "status",
        "update_date",
        "signer",
        "issuing_body",
        "parent_acts",
        "article_titles",
        "citations",
    }

    def __init__(self):
        self.llm = AzureOpenAIService()

    async def chat(
        self,
        db: AsyncSession,
        model_id: UUID,
        question: str,
        extracted_contract: str,
    ) -> dict[str, Any]:
        total_started_at = perf_counter()
        model, model_config = await self._load_model_context(
            db=db,
            model_id=model_id,
        )

        started_at = perf_counter()
        query_prompt = await self._load_prompt(
            db=db,
            prompt_code=PromptCode.LEGAL_CHAT_QUERY_ANALYZER,
        )
        analyzer_result = await self._call_query_analyzer(
            prompt=query_prompt,
            question=question,
            extracted_contract=extracted_contract,
            model_name=model.model_name,
            temperature=float(model_config.temperature),
            max_tokens=int(model_config.max_tokens),
        )
        metadata_seeds = self._validate_analyzer_result(
            analyzer_result
        )
        contract_split_logger.info(
            "[LEGAL_CHAT][TIMING] query_analyzer=%.3fs",
            perf_counter() - started_at,
        )

        started_at = perf_counter()
        legal_context = await asyncio.to_thread(
            LegalChatRetrievalService.retrieve,
            metadata_seeds,
        )
        contract_split_logger.info(
            "[LEGAL_CHAT][TIMING] legal_retrieval=%.3fs",
            perf_counter() - started_at,
        )
        contract_split_logger.info(
            "[LEGAL_CHAT] seeds=%d documents=%d",
            sum(len(values) for values in metadata_seeds.values()),
            len(legal_context),
        )

        sources = [
            {
                "document_id": document["document_id"],
                "metadata": document["metadata"],
            }
            for document in legal_context
        ]

        if not legal_context:
            contract_split_logger.info(
                "[LEGAL_CHAT][TIMING] answer_model=0.000s"
            )
            contract_split_logger.info(
                "[LEGAL_CHAT][TIMING] total=%.3fs",
                perf_counter() - total_started_at,
            )
            return {
                "answer": self.EMPTY_RETRIEVAL_ANSWER,
                "retrieval_seeds": metadata_seeds,
                "sources": sources,
            }

        started_at = perf_counter()
        answer_prompt = await self._load_prompt(
            db=db,
            prompt_code=PromptCode.LEGAL_CHAT_ANSWER,
        )
        answer = await self._call_answer_model(
            prompt=answer_prompt,
            question=question,
            extracted_contract=extracted_contract,
            legal_context=legal_context,
            model_name=model.model_name,
            temperature=float(model_config.temperature),
            max_tokens=int(model_config.max_tokens),
        )
        contract_split_logger.info(
            "[LEGAL_CHAT][TIMING] answer_model=%.3fs",
            perf_counter() - started_at,
        )
        contract_split_logger.info(
            "[LEGAL_CHAT][TIMING] total=%.3fs",
            perf_counter() - total_started_at,
        )

        return {
            "answer": answer,
            "retrieval_seeds": metadata_seeds,
            "sources": sources,
        }

    async def _call_query_analyzer(
        self,
        prompt,
        question: str,
        extracted_contract: str,
        model_name: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        user_prompt = self._render_prompt(
            template=prompt.user_prompt,
            replacements={
                "{{question}}": question,
                "{{extracted_contract}}": extracted_contract,
            },
            prompt_code=PromptCode.LEGAL_CHAT_QUERY_ANALYZER,
        )
        response = await self.llm.chat_json(
            model=model_name,
            messages=self._messages(prompt.system_prompt, user_prompt),
            temperature=temperature,
            max_completion_tokens=max_tokens,
        )
        result = json.loads(response.strip())

        if not isinstance(result, dict):
            raise ValueError(
                "Legal Chat query analyzer response must be an object."
            )

        return result

    async def _call_answer_model(
        self,
        prompt,
        question: str,
        extracted_contract: str,
        legal_context: list[dict[str, Any]],
        model_name: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        user_prompt = self._render_prompt(
            template=prompt.user_prompt,
            replacements={
                "{{question}}": question,
                "{{extracted_contract}}": extracted_contract,
                "{{legal_context}}": json.dumps(
                    legal_context,
                    ensure_ascii=False,
                ),
            },
            prompt_code=PromptCode.LEGAL_CHAT_ANSWER,
        )

        return await self.llm.chat(
            model=model_name,
            messages=self._messages(prompt.system_prompt, user_prompt),
            temperature=temperature,
            max_completion_tokens=max_tokens,
        )

    @classmethod
    def _validate_analyzer_result(
        cls,
        result: Any,
    ) -> dict[str, list[str]]:
        if not isinstance(result, dict):
            raise ValueError(
                "Legal Chat query analyzer response must be an object."
            )

        metadata_seeds = result.get("metadata_seeds")

        if not isinstance(metadata_seeds, dict):
            raise ValueError("metadata_seeds must be an object.")

        normalized = {}
        seed_count = 0

        for field, values in metadata_seeds.items():
            if field not in cls.ALLOWED_METADATA_FIELDS:
                continue

            if not isinstance(values, list):
                raise ValueError(
                    f"Metadata seeds for {field} must be a list."
                )

            normalized_values = []

            for value in values:
                if seed_count >= cls.MAX_RETRIEVAL_SEEDS:
                    break

                if not isinstance(value, str):
                    continue

                value = value.strip()

                if not value:
                    continue

                normalized_values.append(value)
                seed_count += 1

            if normalized_values:
                normalized[field] = normalized_values

            if seed_count >= cls.MAX_RETRIEVAL_SEEDS:
                break

        if not normalized:
            raise ValueError(
                "metadata_seeds must contain at least one valid seed."
            )

        return normalized

    @staticmethod
    def _render_prompt(
        template: str,
        replacements: dict[str, str],
        prompt_code: PromptCode,
    ) -> str:
        rendered = template

        for placeholder, value in replacements.items():
            if placeholder not in rendered:
                raise ValueError(
                    f"Prompt {prompt_code.value} is missing "
                    f"placeholder {placeholder}."
                )

            rendered = rendered.replace(placeholder, value)

        return rendered

    @staticmethod
    def _messages(
        system_prompt: str,
        user_prompt: str,
    ) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    @staticmethod
    async def _load_model_context(
        db: AsyncSession,
        model_id: UUID,
    ):
        model = await AIModelRepository.get_by_id(db=db, id=model_id)

        if model is None:
            raise LookupError("AI model not found.")

        model_config = await (
            WorkspaceConfigRepository
            .get_model_config_by_workspace_code(
                db=db,
                workspace_code=PromptCode.CONTRACT_ANALYZE.value,
            )
        )

        if model_config is None:
            raise LookupError(
                "Workspace model config for CONTRACT_ANALYZE not found."
            )

        return model, model_config

    @staticmethod
    async def _load_prompt(
        db: AsyncSession,
        prompt_code: PromptCode,
    ):
        prompt = await AIPromptRepository.get_by_code(
            db=db,
            code=prompt_code,
        )

        if prompt is None:
            raise LookupError(
                f"Prompt {prompt_code.value} not found."
            )

        return prompt
