import asyncio
from time import perf_counter
from typing import Any

from backend.app.modules.company.contract.contract_advanced_logging import (
    contract_advanced_logger as logger,
)
from backend.app.shared.azure.azure_search_service import (
    AzureSearchService,
)


class CompanyPolicyRetrievalService:

    TOP_K_PER_SEED = 1
    COMPANY_RETRIEVAL_CONCURRENCY = 6

    @classmethod
    async def retrieve(
        cls,
        company_rule_checks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        if not company_rule_checks:
            return []

        semaphore = asyncio.Semaphore(
            cls.COMPANY_RETRIEVAL_CONCURRENCY
        )

        results = await asyncio.gather(
            *[
                cls._retrieve_check(
                    check_index=check_index,
                    check_count=len(company_rule_checks),
                    check=check,
                    semaphore=semaphore,
                )
                for check_index, check in enumerate(
                    company_rule_checks,
                    start=1,
                )
            ]
        )

        return list(results)

    @classmethod
    async def _retrieve_check(
        cls,
        check_index: int,
        check_count: int,
        check: dict[str, Any],
        semaphore: asyncio.Semaphore,
    ) -> dict[str, Any]:

        retrieval_seeds = check.get(
            "retrieval_seeds",
            [],
        )
        if not isinstance(retrieval_seeds, list):
            retrieval_seeds = []

        seeds = [
            seed.strip()
            for seed in retrieval_seeds
            if isinstance(seed, str)
            and seed.strip()
        ][:1]

        contexts = []
        context_keys = set()

        for seed in seeds:
            started_at = perf_counter()
            logger.info(
                "[CONTRACT_ADVANCED] company_retrieval started "
                "check=%d/%d query=%s",
                check_index,
                check_count,
                seed,
            )

            async with semaphore:
                results = await asyncio.to_thread(
                    AzureSearchService.retrieve_contract_policy,
                    question=seed,
                    top_k=cls.TOP_K_PER_SEED,
                )

            logger.info(
                "[CONTRACT_ADVANCED] company_retrieval completed "
                "check=%d/%d in %.3fs result_count=%d",
                check_index,
                check_count,
                perf_counter() - started_at,
                len(results),
            )

            for context in results:
                context_key = cls._context_key(
                    context
                )

                if context_key in context_keys:
                    continue

                context_keys.add(context_key)
                contexts.append(context)

        return {
            "contract_text": check["contract_text"],
            "contexts": contexts,
        }

    @staticmethod
    def _context_key(
        context: dict[str, Any],
    ) -> tuple[str, ...]:

        chunk_id = context.get("chunk_id")

        if chunk_id:
            return (
                "chunk_id",
                str(chunk_id),
            )

        return (
            "parent_content",
            str(context.get("parent_id") or ""),
            str(context.get("content") or ""),
        )
