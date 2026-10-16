import asyncio
import json
from time import perf_counter
from typing import Any, AsyncIterator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.company.contract.contract_advanced_logging import contract_split_logger
from backend.app.modules.configuration.enums.prompt_code import PromptCode
from backend.app.modules.configuration.repositories.ai_model_repository import AIModelRepository
from backend.app.modules.configuration.repositories.ai_prompt_repository import AIPromptRepository
from backend.app.modules.configuration.repositories.rag_config_repository import (
    WorkspaceConfigRepository,
)
from backend.app.modules.company.contract.services.legal_azure_search_retrieval_service import (
    LegalAzureSearchRetrievalService,
)
from backend.app.shared.llm.azure_openai_service import AzureOpenAIService


class LegalContractAnalysisService:
    MAX_LEGAL_CHECKS = 8
    MAX_SEEDS_PER_METADATA_FIELD = 2
    MAX_SEEDS = 2
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

    async def analyze(
        self,
        db: AsyncSession,
        model_id: UUID,
        output_extract: str,
    ) -> AsyncIterator[dict[str, Any]]:
        total_started_at = perf_counter()
        model, model_config = await self._load_model_context(
            db=db,
            model_id=model_id,
        )

        started_at = perf_counter()
        analyzer_prompt = await self._load_prompt(
            db=db,
            prompt_code=PromptCode.LEGAL_CONTRACT_ANALYZER,
        )
        analyzer_result = await self._call_analyzer(
            prompt=analyzer_prompt,
            output_extract=output_extract,
            model_name=model.model_name,
            temperature=float(model_config.temperature),
            max_tokens=int(model_config.max_tokens),
        )
        legal_checks = self._validate_analyzer_result(analyzer_result)
        contract_split_logger.info(
            "[LEGAL_CONTRACT][TIMING] analyzer=%.3fs checks=%d",
            perf_counter() - started_at,
            len(legal_checks),
        )

        if not legal_checks:
            yield {"event": "started", "data": {"total": 0}}
            contract_split_logger.info(
                "[LEGAL_CONTRACT][TIMING] total=%.3fs",
                perf_counter() - total_started_at,
            )
            yield {"event": "completed", "data": {"total": 0}}
            return

        reviewer_prompt = await self._load_prompt(
            db=db,
            prompt_code=PromptCode.LEGAL_CONTRACT_REVIEWER,
        )
        total = len(legal_checks)
        yield {"event": "started", "data": {"total": total}}

        for index, check in enumerate(legal_checks):
            check_started_at = perf_counter()
            reviewer_timed = False

            try:
                retrieval_started_at = perf_counter()
                try:
                    documents = await asyncio.to_thread(
                        LegalAzureSearchRetrievalService.retrieve,
                        check["seeds"],
                    )
                finally:
                    contract_split_logger.info(
                        "[LEGAL_CONTRACT][CHECK %d/%d] retrieval=%.3fs",
                        index + 1,
                        total,
                        perf_counter() - retrieval_started_at,
                    )

                review_item = {
                    "contract_text": check["contract_text"],
                    "legal_context": documents,
                }
                reviewer_started_at = perf_counter()
                try:
                    reviewer_result = await self._call_reviewer(
                        prompt=reviewer_prompt,
                        review_data=review_item,
                        model_name=model.model_name,
                        temperature=float(model_config.temperature),
                        max_tokens=int(model_config.max_tokens),
                    )
                    result = self._validate_reviewer_result(
                        reviewer_result,
                        check["contract_text"],
                    )
                finally:
                    contract_split_logger.info(
                        "[LEGAL_CONTRACT][CHECK %d/%d] reviewer=%.3fs",
                        index + 1,
                        total,
                        perf_counter() - reviewer_started_at,
                    )
                    reviewer_timed = True
                yield {
                    "event": "result",
                    "data": {
                        "index": index,
                        "total": total,
                        "result": result,
                    },
                }
            except Exception as exc:
                contract_split_logger.exception(
                    "[LEGAL_CONTRACT][CHECK %d/%d] failed",
                    index + 1,
                    total,
                )
                yield {
                    "event": "error",
                    "data": {
                        "index": index,
                        "total": total,
                        "check": check,
                        "error": str(exc),
                    },
                }
            finally:
                if not reviewer_timed:
                    contract_split_logger.info(
                        "[LEGAL_CONTRACT][CHECK %d/%d] reviewer=0.000s",
                        index + 1,
                        total,
                    )
                contract_split_logger.info(
                    "[LEGAL_CONTRACT][CHECK %d/%d] total=%.3fs",
                    index + 1,
                    total,
                    perf_counter() - check_started_at,
                )

        contract_split_logger.info(
            "[LEGAL_CONTRACT][TIMING] total=%.3fs",
            perf_counter() - total_started_at,
        )
        yield {"event": "completed", "data": {"total": total}}

    async def _call_analyzer(
        self,
        prompt,
        output_extract: str,
        model_name: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        user_prompt = self._render_prompt(
            template=prompt.user_prompt,
            replacements={
                "{{extracted_contract}}": output_extract,
            },
            prompt_code=PromptCode.LEGAL_CONTRACT_ANALYZER,
        )
        response = await self.llm.chat_json(
            model=model_name,
            messages=self._messages(prompt.system_prompt, user_prompt),
            temperature=temperature,
            max_completion_tokens=max_tokens,
        )

        return self._parse_json_object(response)

    async def _call_reviewer(
        self,
        prompt,
        review_data: dict[str, Any],
        model_name: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        user_prompt = self._render_prompt(
            template=prompt.user_prompt,
            replacements={
                "{{legal_review_data}}": json.dumps(
                    review_data,
                    ensure_ascii=False,
                ),
            },
            prompt_code=PromptCode.LEGAL_CONTRACT_REVIEWER,
        )
        response = await self.llm.chat_json(
            model=model_name,
            messages=self._messages(prompt.system_prompt, user_prompt),
            temperature=temperature,
            max_completion_tokens=max_tokens,
        )

        return self._parse_json_object(response)

    @classmethod
    def _validate_analyzer_result(
        cls,
        result: Any,
    ) -> list[dict[str, Any]]:
        if not isinstance(result, dict):
            raise ValueError(
                "Legal Contract Analyzer response must be an object."
            )

        checks = result.get("legal_checks")

        if not isinstance(checks, list):
            raise ValueError("legal_checks must be a list.")

        return [
            cls._validate_legal_check(check)
            for check in checks[:cls.MAX_LEGAL_CHECKS]
        ]

    @classmethod
    def _validate_legal_check(cls, check: Any) -> dict[str, Any]:
        if not isinstance(check, dict):
            raise ValueError("Each legal check must be an object.")

        contract_text = check.get("contract_text")
        if contract_text is None:
            contract_text = check.get("content")

        if (
            not isinstance(contract_text, str)
            or not contract_text.strip()
        ):
            raise ValueError(
                "Legal check contract_text must be a non-empty string."
            )

        # Accept the new flat "seeds" list and the older "metadata_seeds"
        # (object or list), so the shared DB prompt can return either shape.
        raw_seeds = check.get("seeds")
        if raw_seeds is None:
            raw_seeds = check.get("metadata_seeds")

        seeds = cls._normalize_seeds(raw_seeds)

        if not seeds:
            raise ValueError(
                "Legal check must contain at least one non-empty seed."
            )

        return {
            "contract_text": contract_text,
            "seeds": seeds,
        }

    @classmethod
    def _normalize_seeds(cls, raw_seeds: Any) -> list[str]:
        if isinstance(raw_seeds, str):
            values: list[Any] = [raw_seeds]
        elif isinstance(raw_seeds, list):
            values = raw_seeds
        elif isinstance(raw_seeds, dict):
            values = []
            for item in raw_seeds.values():
                if isinstance(item, list):
                    values.extend(item)
                elif isinstance(item, str):
                    values.append(item)
        else:
            raise ValueError(
                "Legal check seeds must be a list or an object."
            )

        normalized: list[str] = []
        seen: set[str] = set()

        for value in values:
            if not isinstance(value, str):
                continue

            value = value.strip()
            key = value.casefold()

            if not value or key in seen:
                continue

            seen.add(key)
            normalized.append(value)

            if len(normalized) >= cls.MAX_SEEDS:
                break

        return normalized

    @staticmethod
    def _validate_reviewer_result(
        result: Any,
        expected_contract_text: str,
    ) -> dict[str, Any]:
        if not isinstance(result, dict):
            raise ValueError(
                "Legal Contract Reviewer response must be an object."
            )

        item = result.get("result")

        if not isinstance(item, dict):
            raise ValueError("Legal reviewer result must be an object.")

        contract_text = item.get("contract_text")
        status = item.get("status")
        explanation = item.get("explanation")
        recommendation = item.get("recommendation")
        sources = item.get("sources")

        if contract_text != expected_contract_text:
            raise ValueError(
                "Reviewer result contract_text does not match the "
                "current legal check."
            )

        if status not in {"COMPLIANT", "RISK", "UNCLEAR"}:
            raise ValueError("Reviewer result status is invalid.")

        if not isinstance(explanation, str):
            raise ValueError(
                "Reviewer result explanation must be a string."
            )

        if not isinstance(recommendation, str):
            raise ValueError(
                "Reviewer result recommendation must be a string."
            )

        if not isinstance(sources, list):
            raise ValueError("Reviewer result sources must be a list.")

        return {
            "contract_text": contract_text,
            "status": status,
            "explanation": explanation,
            "recommendation": recommendation,
            "sources": [
                {
                    key: value
                    for key, value in source.items()
                    if key != "vn_text"
                }
                for source in sources
                if isinstance(source, dict)
            ],
        }

    @staticmethod
    def _parse_json_object(response: str) -> dict[str, Any]:
        content = response.strip()

        if content.startswith("```"):
            lines = content.splitlines()[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            content = "\n".join(lines).strip()

        result = json.loads(content)

        if not isinstance(result, dict):
            raise ValueError("LLM response must be a JSON object.")

        return result

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
