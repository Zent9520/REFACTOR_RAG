"""Mock load test for the retrieval concurrency gates.

This test exercises the real ``AzureSearchService.retrieve`` orchestration,
but replaces Azure OpenAI and Azure AI Search with deterministic fakes. It
does not consume Azure quota, write to the database, or require network access.

Run from ``D:\\RAG_INTERN``:

    .\\backend\\venv\\Scripts\\python.exe -m pytest \
        backend\\tests\\services\\azure\\test_azure_search_concurrency_load.py \
        -q -s --log-cli-level=INFO
"""

import asyncio
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.core.settings import settings
from backend.app.shared.resilience.capacity_manager import CapacityManager
import backend.app.shared.azure.azure_search_service as search_module


class LoadMetrics:
    def __init__(self):
        self.embedding_active = 0
        self.embedding_max = 0
        self.embedding_calls = 0
        self.search_active = 0
        self.search_max = 0
        self.search_calls = 0

    async def embedding(self):
        self.embedding_active += 1
        self.embedding_calls += 1
        self.embedding_max = max(
            self.embedding_max,
            self.embedding_active,
        )
        try:
            # Fast enough to feed the Search queue without making the test slow.
            await asyncio.sleep(0.005)
            return SimpleNamespace(
                data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3])]
            )
        finally:
            self.embedding_active -= 1

    async def search(self, search_text):
        self.search_active += 1
        self.search_calls += 1
        self.search_max = max(self.search_max, self.search_active)

        try:
            await asyncio.sleep(0.05)
            if search_text == "*":
                return [{
                    "@search.score": 1.0,
                    "chunk_id": "chunk-1",
                    "parent_id": "document-1",
                    "title": "Mock document",
                    "chunk": "Mock document content",
                    "source_file": "mock.pdf",
                    "department": "Legal",
                    "sensitivity": 1,
                }]

            return [{
                "@search.score": 1.0,
                "chunk_id": "top-chunk",
                "parent_id": "document-1",
                "title": "Mock document",
            }]
        finally:
            self.search_active -= 1


class FakeEmbeddings:
    def __init__(self, metrics):
        self.metrics = metrics

    async def create(self, **_kwargs):
        return await self.metrics.embedding()


class FakeAsyncAzureOpenAI:
    def __init__(self, metrics, **_kwargs):
        self.embeddings = FakeEmbeddings(metrics)

    async def close(self):
        return None


class FakeSearchClient:
    def __init__(self, metrics, **_kwargs):
        self.metrics = metrics

    async def search(self, search_text=None, **_kwargs):
        documents = await self.metrics.search(search_text)
        return FakeAsyncSearchResults(documents)

    async def close(self):
        return None


class FakeAsyncSearchResults:
    def __init__(self, documents):
        self._documents = documents
        self._index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._index >= len(self._documents):
            raise StopAsyncIteration
        document = self._documents[self._index]
        self._index += 1
        return document


class AzureSearchConcurrencyLoadTest(unittest.IsolatedAsyncioTestCase):
    async def test_100_retrievals_use_12_embedding_and_20_search_slots(self):
        request_count = 100
        metrics = LoadMetrics()

        with (
            patch.object(settings, "AZURE_SEARCH_MAX_CONCURRENCY", 20),
            patch.object(settings, "AZURE_SEARCH_QUEUE_TIMEOUT_SECONDS", 5.0),
            patch.object(settings, "AZURE_OPENAI_EMBEDDING_MAX_CONCURRENCY", 12),
            patch.object(
                settings,
                "AZURE_OPENAI_EMBEDDING_QUEUE_TIMEOUT_SECONDS",
                5.0,
            ),
        ):
            manager = CapacityManager()

        print(
            "[TEST][RETRIEVAL_LOAD][START] "
            f"requests={request_count} embedding_limit=12 search_limit=20"
        )

        started_at = time.perf_counter()
        with (
            patch.object(search_module, "capacity_manager", manager),
            patch.object(
                search_module,
                "AsyncAzureOpenAI",
                side_effect=lambda **kwargs: FakeAsyncAzureOpenAI(
                    metrics,
                    **kwargs,
                ),
            ),
            patch.object(
                search_module,
                "AsyncSearchClient",
                side_effect=lambda **kwargs: FakeSearchClient(
                    metrics,
                    **kwargs,
                ),
            ),
        ):
            results = await asyncio.gather(*(
                search_module.AzureSearchService.retrieve(
                    question=f"Simple question {index}",
                    group_ids=["group-load-test"],
                    permissions=[{
                        "department": "Legal",
                        "max_sensitivity": 2,
                    }],
                    rewrite_query=False,
                )
                for index in range(request_count)
            ))

        elapsed = time.perf_counter() - started_at
        successful = sum(bool(result) for result in results)

        print(
            "[TEST][RETRIEVAL_LOAD][RESULT] "
            f"successful={successful}/{request_count} "
            f"embedding_calls={metrics.embedding_calls} "
            f"embedding_max_active={metrics.embedding_max}/12 "
            f"search_calls={metrics.search_calls} "
            f"search_max_active={metrics.search_max}/20 "
            f"elapsed={elapsed:.3f}s"
        )

        self.assertEqual(successful, request_count)
        self.assertEqual(metrics.embedding_calls, request_count)
        self.assertEqual(
            metrics.embedding_max,
            12,
            "The mock load must saturate all 12 embedding slots.",
        )

        # Each retrieval performs one top-chunk search and one document-chunk
        # search, so 100 requests produce 200 Search calls.
        self.assertEqual(metrics.search_calls, request_count * 2)
        self.assertEqual(
            metrics.search_max,
            20,
            "Async Azure Search must saturate all 20 Search slots.",
        )

        self.assertEqual(manager.embedding._active, 0)
        self.assertEqual(manager.search._active, 0)
        self.assertEqual(manager.embedding._waiting, 0)
        self.assertEqual(manager.search._waiting, 0)

        print(
            "[TEST][RETRIEVAL_LOAD][CLEANUP] "
            "embedding_active=0 search_active=0 waiting=0; "
            "no semaphore permit leaked"
        )


if __name__ == "__main__":
    unittest.main()
