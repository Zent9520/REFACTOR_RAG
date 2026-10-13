import asyncio
import json
from collections import Counter
from time import perf_counter
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.modules.contract.contract_advanced_logging import (
    contract_advanced_logger as logger,
    contract_split_logger,
)
from backend.app.modules.configuration.enums.prompt_code import PromptCode
from backend.app.modules.configuration.repositories.ai_model_repository import (
    AIModelRepository,
)
from backend.app.modules.configuration.repositories.ai_prompt_repository import (
    AIPromptRepository,
)
from backend.app.modules.configuration.repositories.rag_config_repository import (
    WorkspaceConfigRepository,
)
from backend.app.modules.contract.services.company_policy_retrieval_service import (
    CompanyPolicyRetrievalService,
)
from backend.app.modules.contract.services.legal_retrieval_service import (
    LegalRetrievalService,
)
from backend.app.shared.llm.azure_openai_service import (
    AzureOpenAIService,
    LLMResponseTruncatedError,
)
from backend.app.shared.azure.document_intelligent import (
    DocumentExtractor,
)

class ContractAdvancedService:

    def __init__(self):
        self.llm = AzureOpenAIService()

    async def analyze(
        self,
        db: AsyncSession,
        file_path: str,
        model_id: UUID,
    ) -> dict[str, Any]:

        request_started_at = perf_counter()
        logger.info(
            "=" * 100
        )
        logger.info(
            "[CONTRACT_ADVANCED] request started model_id=%s",
            model_id,
        )

        started_at = perf_counter()
        model = await AIModelRepository.get_by_id(
            db=db,
            id=model_id,
        )
        logger.info(
            "[CONTRACT_ADVANCED] load_model completed in %.3fs",
            perf_counter() - started_at,
        )

        if model is None:
            raise LookupError("AI model not found.")

        started_at = perf_counter()
        model_config = await (
            WorkspaceConfigRepository
            .get_model_config_by_workspace_code(
                db=db,
                workspace_code=PromptCode.CONTRACT_ANALYZE.value,
            )
        )
        logger.info(
            "[CONTRACT_ADVANCED] load_model_config completed in %.3fs",
            perf_counter() - started_at,
        )

        if model_config is None:
            raise LookupError(
                "Workspace model config for CONTRACT_ANALYZE not found."
            )

        started_at = perf_counter()
        contract_content = self._extract_contract(
            file_path
        )
        logger.info(
            "[CONTRACT_ADVANCED][TIMING] extract_contract=%.3fs",
            perf_counter() - started_at,
        )

        started_at = perf_counter()
        analysis = await self._analyze_contract_for_retrieval(
            db=db,
            contract_content=contract_content,
            model_name=model.model_name,
            temperature=float(model_config.temperature),
            max_tokens=int(model_config.max_tokens),
        )
        logger.info(
            "[CONTRACT_ADVANCED][TIMING] analyzer=%.3fs",
            perf_counter() - started_at,
        )

        company_rule_checks = analysis[
            "company_rule_checks"
        ]
        legal_checks = analysis[
            "legal_checks"
        ]
        logger.info(
            "[CONTRACT_ADVANCED] company_checks=%d legal_checks=%d",
            len(company_rule_checks),
            len(legal_checks),
        )

        company_prompt = (
            await self._load_prompt(
                db=db,
                prompt_code=(
                    PromptCode.CONTRACT_COMPANY_RULE_REVIEWER
                ),
            )
            if company_rule_checks
            else None
        )
        legal_prompt = (
            await self._load_prompt(
                db=db,
                prompt_code=PromptCode.CONTRACT_LEGAL_REVIEWER,
            )
            if legal_checks
            else None
        )

        company_rule_review, legal_review = await asyncio.gather(
            self._process_company_pipeline(
                db=db,
                company_rule_checks=company_rule_checks,
                prompt=company_prompt,
                model_name=model.model_name,
                temperature=float(model_config.temperature),
                max_tokens=int(model_config.max_tokens),
            ),
            self._process_legal_pipeline(
                db=db,
                legal_checks=legal_checks,
                prompt=legal_prompt,
                model_name=model.model_name,
                temperature=float(model_config.temperature),
                max_tokens=int(model_config.max_tokens),
            ),
        )

        response = {
            "company_rule_review": company_rule_review,
            "legal_review": legal_review,
        }
        logger.info(
            "[CONTRACT_ADVANCED][TIMING] total=%.3fs",
            perf_counter() - request_started_at,
        )

        return response

    async def analyze_company_rule(
        self,
        db: AsyncSession,
        file_path: str,
        model_id: UUID,
    ) -> dict[str, Any]:
        request_started_at = perf_counter()
        contract_split_logger.info(
            "[CONTRACT_COMPANY_RULE] started model_id=%s",
            model_id,
        )
        started_at = perf_counter()
        model, model_config = await self._load_model_context(
            db=db,
            model_id=model_id,
        )
        contract_split_logger.info(
            "[CONTRACT_COMPANY_RULE][TIMING] "
            "load_model_context=%.3fs",
            perf_counter() - started_at,
        )

        started_at = perf_counter()
        contract_content = self._extract_contract(file_path)
        contract_split_logger.info(
            "[CONTRACT_COMPANY_RULE][TIMING] "
            "extract_contract=%.3fs",
            perf_counter() - started_at,
        )

        started_at = perf_counter()
        analysis = await self._analyze_contract_for_company_rules(
            db=db,
            contract_content=contract_content,
            model_name=model.model_name,
            temperature=float(model_config.temperature),
            max_tokens=int(model_config.max_tokens),
        )
        contract_split_logger.info(
            "[CONTRACT_COMPANY_RULE][TIMING] analyzer=%.3fs",
            perf_counter() - started_at,
        )

        company_rule_checks = analysis["company_rule_checks"]
        contract_split_logger.info(
            "[CONTRACT_COMPANY_RULE] company_checks=%d",
            len(company_rule_checks),
        )
        started_at = perf_counter()
        company_prompt = (
            await self._load_prompt(
                db=db,
                prompt_code=(
                    PromptCode.CONTRACT_COMPANY_RULE_REVIEWER
                ),
            )
            if company_rule_checks
            else None
        )
        contract_split_logger.info(
            "[CONTRACT_COMPANY_RULE][TIMING] load_prompt=%.3fs",
            perf_counter() - started_at,
        )
        company_rule_review = await self._process_company_pipeline(
            db=db,
            company_rule_checks=company_rule_checks,
            prompt=company_prompt,
            model_name=model.model_name,
            temperature=float(model_config.temperature),
            max_tokens=int(model_config.max_tokens),
            timing_scope="CONTRACT_COMPANY_RULE",
            timing_logger=contract_split_logger,
        )
        contract_split_logger.info(
            "[CONTRACT_COMPANY_RULE][TIMING] total=%.3fs",
            perf_counter() - request_started_at,
        )

        return {
            "company_rule_review": company_rule_review,
            "contract_content": contract_content,
        }

    async def analyze_legal(
        self,
        db: AsyncSession,
        model_id: UUID,
        legal_checks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        request_started_at = perf_counter()
        contract_split_logger.info(
            "[CONTRACT_LEGAL] started model_id=%s input_checks=%d",
            model_id,
            len(legal_checks),
        )
        started_at = perf_counter()
        model, model_config = await self._load_model_context(
            db=db,
            model_id=model_id,
        )
        contract_split_logger.info(
            "[CONTRACT_LEGAL][TIMING] load_model_context=%.3fs",
            perf_counter() - started_at,
        )
        started_at = perf_counter()
        normalized_legal_checks = self._validate_legal_checks(
            legal_checks
        )
        contract_split_logger.info(
            "[CONTRACT_LEGAL][TIMING] validate_checks=%.3fs "
            "normalized_checks=%d",
            perf_counter() - started_at,
            len(normalized_legal_checks),
        )
        started_at = perf_counter()
        legal_prompt = (
            await self._load_prompt(
                db=db,
                prompt_code=PromptCode.CONTRACT_LEGAL_REVIEWER,
            )
            if normalized_legal_checks
            else None
        )
        contract_split_logger.info(
            "[CONTRACT_LEGAL][TIMING] load_prompt=%.3fs",
            perf_counter() - started_at,
        )
        legal_review = await self._process_legal_pipeline(
            db=db,
            legal_checks=normalized_legal_checks,
            prompt=legal_prompt,
            model_name=model.model_name,
            temperature=float(model_config.temperature),
            max_tokens=int(model_config.max_tokens),
            timing_scope="CONTRACT_LEGAL",
            timing_logger=contract_split_logger,
        )
        contract_split_logger.info(
            "[CONTRACT_LEGAL][TIMING] total=%.3fs",
            perf_counter() - request_started_at,
        )

        return {"legal_review": legal_review}

    @staticmethod
    async def _load_model_context(
        db: AsyncSession,
        model_id: UUID,
    ):
        model = await AIModelRepository.get_by_id(
            db=db,
            id=model_id,
        )

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
    def _extract_contract(
        file_path: str,
    ) -> str:

        extraction = DocumentExtractor.extract(
            file_path
        )
        contract_content = extraction.text.strip()

        if not contract_content:
            raise ValueError(
                "Extracted contract content is empty."
            )

        return contract_content

    async def _process_company_pipeline(
        self,
        db: AsyncSession,
        company_rule_checks: list[dict[str, Any]],
        prompt: Any,
        model_name: str,
        temperature: float,
        max_tokens: int,
        timing_scope: str = "CONTRACT_ADVANCED",
        timing_logger: Any = None,
    ) -> dict[str, Any]:

        pipeline_started_at = perf_counter()
        pipeline_logger = timing_logger or logger

        if not company_rule_checks:
            pipeline_logger.info(
                "[%s][TIMING] company_retrieval=0.000s",
                timing_scope,
            )
            pipeline_logger.info(
                "[%s][TIMING] company_reviewer=0.000s",
                timing_scope,
            )
            pipeline_logger.info(
                "[%s][TIMING] company_pipeline_total=0.000s",
                timing_scope,
            )
            return {"results": []}

        started_at = perf_counter()
        review_data = await (
            CompanyPolicyRetrievalService
            .retrieve(company_rule_checks)
        )
        pipeline_logger.info(
            "[%s][TIMING] company_retrieval=%.3fs",
            timing_scope,
            perf_counter() - started_at,
        )

        review_json = json.dumps(
            review_data,
            ensure_ascii=False,
            indent=2,
        )
        pipeline_logger.info(
            "[%s] company_retrieval_calls=%d "
            "company_review_items=%d company_review_chars=%d",
            timing_scope,
            sum(
                len(check["retrieval_seeds"])
                for check in company_rule_checks
            ),
            len(review_data),
            len(review_json),
        )

        started_at = perf_counter()
        result = await self._review_company_rules(
            db=db,
            review_data=review_data,
            review_json=review_json,
            prompt=prompt,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        pipeline_logger.info(
            "[%s][TIMING] company_reviewer=%.3fs",
            timing_scope,
            perf_counter() - started_at,
        )
        pipeline_logger.info(
            "[%s][TIMING] company_pipeline_total=%.3fs",
            timing_scope,
            perf_counter() - pipeline_started_at,
        )

        return result

    async def _process_legal_pipeline(
        self,
        db: AsyncSession,
        legal_checks: list[dict[str, Any]],
        prompt: Any,
        model_name: str,
        temperature: float,
        max_tokens: int,
        timing_scope: str = "CONTRACT_ADVANCED",
        timing_logger: Any = None,
    ) -> dict[str, Any]:

        pipeline_started_at = perf_counter()
        pipeline_logger = timing_logger or logger

        if not legal_checks:
            pipeline_logger.info(
                "[%s][TIMING] legal_retrieval=0.000s",
                timing_scope,
            )
            pipeline_logger.info(
                "[%s][TIMING] legal_reviewer=0.000s",
                timing_scope,
            )
            pipeline_logger.info(
                "[%s][TIMING] legal_pipeline_total=0.000s",
                timing_scope,
            )
            return {"results": []}

        started_at = perf_counter()
        review_data = await LegalRetrievalService.retrieve_async(
            legal_checks
        )
        pipeline_logger.info(
            "[%s][TIMING] legal_retrieval=%.3fs",
            timing_scope,
            perf_counter() - started_at,
        )

        review_json = json.dumps(
            review_data,
            ensure_ascii=False,
            indent=2,
        )
        pipeline_logger.info(
            "[%s] legal_context_documents=%d "
            "legal_review_items=%d legal_review_chars=%d",
            timing_scope,
            sum(
                len(item["contexts"])
                for item in review_data
            ),
            len(review_data),
            len(review_json),
        )

        started_at = perf_counter()
        result = await self._review_legal(
            db=db,
            review_data=review_data,
            review_json=review_json,
            prompt=prompt,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        pipeline_logger.info(
            "[%s][TIMING] legal_reviewer=%.3fs",
            timing_scope,
            perf_counter() - started_at,
        )
        pipeline_logger.info(
            "[%s][TIMING] legal_pipeline_total=%.3fs",
            timing_scope,
            perf_counter() - pipeline_started_at,
        )

        return result

    async def _analyze_contract_for_retrieval(
        self,
        db: AsyncSession,
        contract_content: str,
        model_name: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:

        result = await self._call_llm_json(
            db=db,
            prompt_code=PromptCode.CONTRACT_REVIEW_ANALYZER,
            placeholder="{{contract_content}}",
            placeholder_value=contract_content,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return self._validate_analyzer_result(
            result
        )

    async def _analyze_contract_for_company_rules(
        self,
        db: AsyncSession,
        contract_content: str,
        model_name: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        result = await self._call_llm_json(
            db=db,
            prompt_code=PromptCode.CONTRACT_REVIEW_ANALYZER,
            placeholder="{{contract_content}}",
            placeholder_value=contract_content,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return self._validate_company_analyzer_result(result)

    async def _review_company_rules(
        self,
        db: AsyncSession,
        review_data: list[dict[str, Any]],
        model_name: str,
        temperature: float,
        max_tokens: int,
        review_json: str | None = None,
        prompt: Any = None,
    ) -> dict[str, Any]:

        if not review_data:
            logger.info(
                "[CONTRACT_ADVANCED] company_reviewer skipped: "
                "no company checks"
            )
            return {"results": []}

        result = await self._call_llm_json(
            db=db,
            prompt_code=(
                PromptCode.CONTRACT_COMPANY_RULE_REVIEWER
            ),
            placeholder="{{company_rule_review_data}}",
            placeholder_value=(
                review_json
                or json.dumps(
                    review_data,
                    ensure_ascii=False,
                    indent=2,
                )
            ),
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt=prompt,
        )

        return self._validate_review_result(
            result=result,
            review_name="Company rule review",
            review_data=review_data,
        )

    async def _review_legal(
        self,
        db: AsyncSession,
        review_data: list[dict[str, Any]],
        model_name: str,
        temperature: float,
        max_tokens: int,
        review_json: str | None = None,
        prompt: Any = None,
    ) -> dict[str, Any]:

        if not review_data:
            logger.info(
                "[CONTRACT_ADVANCED] legal_reviewer skipped: "
                "no legal checks"
            )
            return {"results": []}

        result = await self._call_llm_json(
            db=db,
            prompt_code=PromptCode.CONTRACT_LEGAL_REVIEWER,
            placeholder="{{legal_review_data}}",
            placeholder_value=(
                review_json
                or json.dumps(
                    review_data,
                    ensure_ascii=False,
                    indent=2,
                )
            ),
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt=prompt,
        )

        return self._validate_review_result(
            result=result,
            review_name="Legal review",
            review_data=review_data,
        )

    async def _call_llm_json(
        self,
        db: AsyncSession,
        prompt_code: PromptCode,
        placeholder: str,
        placeholder_value: str,
        model_name: str,
        temperature: float,
        max_tokens: int,
        prompt: Any = None,
    ) -> dict[str, Any]:

        if prompt is None:
            prompt = await self._load_prompt(
                db=db,
                prompt_code=prompt_code,
            )

        if placeholder not in prompt.user_prompt:
            raise ValueError(
                f"Prompt {prompt_code.value} is missing "
                f"placeholder {placeholder}."
            )

        user_prompt = prompt.user_prompt.replace(
            placeholder,
            placeholder_value,
        )
        messages = [
            {
                "role": "system",
                "content": prompt.system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ]

        started_at = perf_counter()
        logger.info(
            "[CONTRACT_ADVANCED] llm_call started "
            "prompt=%s max_tokens=%d",
            prompt_code.value,
            max_tokens,
        )

        try:
            response = await self.llm.chat_json(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_completion_tokens=max_tokens,
            )
            logger.info(
                "[CONTRACT_ADVANCED] llm_call completed "
                "prompt=%s in %.3fs result=%s",
                prompt_code.value,
                perf_counter() - started_at,
                response,
            )

            return self._parse_json_object(
                response
            )
        except (
            json.JSONDecodeError,
            LLMResponseTruncatedError,
        ) as exc:
            logger.error(
                "[CONTRACT_ADVANCED] llm_call failed "
                "without retry prompt=%s in %.3fs error=%s",
                prompt_code.value,
                perf_counter() - started_at,
                exc,
            )
            raise

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

    @staticmethod
    def _parse_json_object(
        response: str,
    ) -> dict[str, Any]:

        content = response.strip()

        if content.startswith("```"):
            lines = content.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            content = "\n".join(lines).strip()

        result = json.loads(content)

        if not isinstance(result, dict):
            raise ValueError(
                "LLM response must be a JSON object."
            )

        return result

    @classmethod
    def _validate_analyzer_result(
        cls,
        result: dict[str, Any],
    ) -> dict[str, Any]:

        company_checks = result.get(
            "company_rule_checks"
        )
        legal_checks = result.get(
            "legal_checks"
        )

        if not isinstance(company_checks, list):
            raise ValueError(
                "company_rule_checks must be a list."
            )

        if not isinstance(legal_checks, list):
            raise ValueError(
                "legal_checks must be a list."
            )

        return {
            "company_rule_checks": [
                cls._validate_company_check(item)
                for item in company_checks[:8]
            ],
            "legal_checks": [
                cls._validate_legal_check(item)
                for item in legal_checks[:8]
            ],
        }

    @classmethod
    def _validate_company_analyzer_result(
        cls,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        company_checks = result.get("company_rule_checks")

        if not isinstance(company_checks, list):
            raise ValueError(
                "company_rule_checks must be a list."
            )

        return {
            "company_rule_checks": [
                cls._validate_company_check(item)
                for item in company_checks[:8]
            ]
        }

    @classmethod
    def _validate_legal_checks(
        cls,
        legal_checks: Any,
    ) -> list[dict[str, Any]]:
        if not isinstance(legal_checks, list):
            raise ValueError("legal_checks must be a list.")

        return [
            cls._validate_legal_check(item)
            for item in legal_checks[:8]
        ]

    @classmethod
    def _validate_company_check(
        cls,
        item: Any,
    ) -> dict[str, Any]:

        if not isinstance(item, dict):
            raise ValueError(
                "Each company rule check must be an object."
            )

        contract_text = item.get("contract_text")
        retrieval_seeds = item.get("retrieval_seeds")

        if (
            not isinstance(contract_text, str)
            or not contract_text.strip()
        ):
            raise ValueError(
                "Company check contract_text must be a non-empty string."
            )

        normalized_seeds = cls._normalize_string_list(
            retrieval_seeds,
            "Company check retrieval_seeds",
        )

        if not normalized_seeds:
            raise ValueError(
                "Company check retrieval_seeds must contain "
                "exactly one seed."
            )

        return {
            "contract_text": contract_text,
            "retrieval_seeds": [normalized_seeds[0]],
        }

    @classmethod
    def _validate_legal_check(
        cls,
        item: Any,
    ) -> dict[str, Any]:

        if not isinstance(item, dict):
            raise ValueError(
                "Each legal check must be an object."
            )

        contract_text = item.get("contract_text")
        metadata_seeds = item.get("metadata_seeds")

        if (
            not isinstance(contract_text, str)
            or not contract_text.strip()
        ):
            raise ValueError(
                "Legal check contract_text must be a non-empty string."
            )

        if not isinstance(metadata_seeds, dict):
            raise ValueError(
                "Legal check metadata_seeds must be an object."
            )

        normalized_seeds = {}

        for metadata_type, seeds in metadata_seeds.items():
            if not isinstance(metadata_type, str):
                raise ValueError(
                    "Legal metadata seed keys must be strings."
                )

            if (
                metadata_type
                not in LegalRetrievalService.SUPPORTED_METADATA_FIELDS
            ):
                continue

            normalized_values = cls._normalize_string_list(
                seeds,
                f"Legal metadata seeds for {metadata_type}",
            )[:1]

            if normalized_values:
                normalized_seeds[metadata_type] = (
                    normalized_values
                )

        return {
            "contract_text": contract_text,
            "metadata_seeds": normalized_seeds,
        }

    @staticmethod
    def _normalize_string_list(
        value: Any,
        field_name: str,
    ) -> list[str]:

        if not isinstance(value, list):
            raise ValueError(
                f"{field_name} must be a list."
            )

        normalized = []

        for item in value:
            if item is None:
                continue

            if not isinstance(item, str):
                raise ValueError(
                    f"{field_name} must contain only strings."
                )

            item = item.strip()

            if item:
                normalized.append(item)

        return normalized

    @staticmethod
    def _validate_review_result(
        result: dict[str, Any],
        review_name: str,
        review_data: list[dict[str, Any]],
    ) -> dict[str, Any]:

        results = result.get("results")

        if not isinstance(results, list):
            raise ValueError(
                f"{review_name} results must be a list."
            )

        result_contract_texts = []

        for item in results:
            if not isinstance(item, dict):
                raise ValueError(
                    f"Each {review_name} result must be an object."
                )

            contract_text = item.get("contract_text")

            if not isinstance(contract_text, str):
                raise ValueError(
                    f"Each {review_name} result must contain "
                    "contract_text."
                )

            result_contract_texts.append(contract_text)

        expected_contract_texts = [
            item["contract_text"]
            for item in review_data
        ]

        if Counter(result_contract_texts) != Counter(
            expected_contract_texts
        ):
            raise ValueError(
                f"{review_name} results do not match "
                "the analyzed contract checks."
            )

        return result
