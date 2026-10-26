import asyncio
import json
import logging
import time

from app.core.timing import timed
from azure.search.documents import SearchClient as SyncSearchClient
from azure.search.documents.aio import SearchClient as AsyncSearchClient

from azure.search.documents.models import (
    VectorizedQuery
)

from azure.core.credentials import (
    AzureKeyCredential
)

from openai import (
    AsyncAzureOpenAI,
    AzureOpenAI,
)

from app.core.settings import settings

from app.modules.configuration.repositories.rag_config_repository import (
    WorkspaceConfigRepository
)
from app.modules.configuration.enums.prompt_code import PromptCode

from app.shared.llm.azure_openai_service import AzureOpenAIService
from app.shared.resilience.capacity_manager import capacity_manager
from app.shared.resilience.retry_policy import retry_async


logger = logging.getLogger(__name__)


class AzureSearchService:
    _embedding_client: AsyncAzureOpenAI | None = None
    _search_client: AsyncSearchClient | None = None

    @classmethod
    def _get_embedding_client(cls) -> AsyncAzureOpenAI:
        if cls._embedding_client is None:
            cls._embedding_client = AsyncAzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                max_retries=0,
            )
        return cls._embedding_client

    @classmethod
    def _get_search_client(cls) -> AsyncSearchClient:
        if cls._search_client is None:
            cls._search_client = AsyncSearchClient(
                endpoint=settings.AZURE_SEARCH_ENDPOINT,
                index_name=settings.AZURE_SEARCH_INDEX,
                credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY),
            )
        return cls._search_client

    @classmethod
    async def close_shared_clients(cls) -> None:
        embedding_client, search_client = cls._embedding_client, cls._search_client
        cls._embedding_client = None
        cls._search_client = None
        try:
            if embedding_client is not None:
                await embedding_client.close()
        finally:
            if search_client is not None:
                await search_client.close()

    @staticmethod
    async def warm_up() -> None:
        """Best-effort startup probes for the chat embedding and Search index."""
        async def warm_embedding() -> None:
            started = time.perf_counter()
            try:
                client = AzureSearchService._get_embedding_client()
                async with capacity_manager.embedding_slot():
                    await asyncio.wait_for(
                        client.embeddings.create(
                            model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                            input="warmup",
                        ),
                        timeout=settings.AZURE_OPENAI_EMBEDDING_REQUEST_TIMEOUT_SECONDS,
                    )
                logger.info("[warmup] embedding ready in %.2fs", time.perf_counter() - started)
            except Exception:
                logger.exception("[warmup] embedding failed")

        async def warm_search() -> None:
            started = time.perf_counter()
            try:
                client = AzureSearchService._get_search_client()
                async with capacity_manager.search_slot():
                    await asyncio.wait_for(
                        AzureSearchService._search_async(
                            client,
                            search_text="*",
                            filter="chunk_id eq '__warm_up__'",
                            select=["chunk_id"],
                            top=1,
                        ),
                        timeout=settings.AZURE_SEARCH_REQUEST_TIMEOUT_SECONDS,
                    )
                logger.info("[warmup] search ready in %.2fs", time.perf_counter() - started)
            except Exception:
                logger.exception("[warmup] search failed")

        await asyncio.gather(warm_embedding(), warm_search())

    @staticmethod
    async def _search_async(client: AsyncSearchClient, **kwargs) -> list:
        """Collect one Azure async search page without using a thread pool."""

        results = await client.search(**kwargs)
        return [document async for document in results]

    @staticmethod
    def _escape_odata_value(value: str) -> str:

        return value.replace("'", "''")

    @staticmethod
    def build_acl_filter(
        group_ids: list[str],
        permissions: list[dict],
    ) -> str:
        normalized_group_ids = []
        seen_group_ids = set()

        for group_id in group_ids:
            group_id = str(group_id).strip()

            if not group_id or group_id in seen_group_ids:
                continue

            seen_group_ids.add(group_id)
            normalized_group_ids.append(
                AzureSearchService
                ._escape_odata_value(group_id)
            )

        if not normalized_group_ids:
            raise ValueError("group_ids must not be empty.")

        group_conditions = " or ".join(
            f"g eq '{group_id}'"
            for group_id in normalized_group_ids
        )
        group_filter = (
            "allowed_group_ids/any("
            f"g: {group_conditions}"
            ")"
        )

        permission_by_department: dict[str, int] = {}

        for permission in permissions:
            department = str(
                permission.get("department") or ""
            ).strip()
            max_sensitivity = permission.get("max_sensitivity")

            if not department or isinstance(max_sensitivity, bool):
                continue

            try:
                max_sensitivity = int(max_sensitivity)
            except (TypeError, ValueError):
                continue

            current_max = permission_by_department.get(department)

            if current_max is None or max_sensitivity > current_max:
                permission_by_department[department] = max_sensitivity

        if not permission_by_department:
            raise ValueError("permissions must not be empty.")

        permission_conditions = " or ".join(
            "(department eq "
            f"'{AzureSearchService._escape_odata_value(department)}' "
            f"and sensitivity le {max_sensitivity})"
            for department, max_sensitivity in permission_by_department.items()
        )

        return (
            f"({group_filter}) "
            f"and ({permission_conditions})"
        )
    
    
    
    
    @staticmethod
    async def analyze_question_to_query(question: str) -> str:

        prompt = f"""
    Bạn là bộ viết lại câu hỏi (query rewriting) cho hệ thống retrieval tài liệu nội bộ.

    Nhiệm vụ: đọc câu hỏi của người dùng và viết lại thành 1 đoạn văn ngắn,
    dùng để tìm kiếm full-text (BM25) trong kho tài liệu, sao cho dễ khớp
    với nội dung chunk tài liệu gốc nhất có thể.

    Yêu cầu:
    - Chỉ trả về đúng 1 đoạn văn bản thuần (plain text), KHÔNG JSON, KHÔNG markdown, không giải thích gì thêm.
    - Giữ nguyên ngôn ngữ của câu hỏi gốc.
    - Có thể mở rộng thêm từ đồng nghĩa / thuật ngữ liên quan nếu giúp tăng khả năng match,
    nhưng không lan man, không thêm ý ngoài phạm vi câu hỏi.

    Câu hỏi: "{question}"

    Đoạn văn tìm kiếm:
    """

        result = await (
            AzureOpenAIService()
            .generate(
                model="gpt-5.1",
                prompt=prompt,
                temperature=0.2,
            )
        )

        logger.info("Rewritten search query: %s", result)

        search_text_query = result.strip() if result else question

        return search_text_query


   
    @staticmethod
    async def retrieve(
        question: str,
        group_ids: list[str],
        permissions: list[dict],
        rewrite_query: bool = True,
    ):
        acl_filter = AzureSearchService.build_acl_filter(
            group_ids=group_ids,
            permissions=permissions,
        )
        search_text_query = question
        if rewrite_query:
            with timed("retrieval.search_rewrite"):
                search_text_query = await AzureSearchService.analyze_question_to_query(
                    question
                )

        openai_client = AzureSearchService._get_embedding_client()
        with timed("retrieval.embedding"):
            async with capacity_manager.embedding_slot():
                embedding_response = await retry_async(
                    lambda: asyncio.wait_for(
                        openai_client.embeddings.create(
                            model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                            input=question,
                        ),
                        timeout=settings.AZURE_OPENAI_EMBEDDING_REQUEST_TIMEOUT_SECONDS,
                    ),
                    operation_name="azure_openai.embedding",
                )

        query_embedding = embedding_response.data[0].embedding
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=10,
            fields="text_vector",
        )

        client = AzureSearchService._get_search_client()
        with timed("retrieval.search"):
            async with capacity_manager.search_slot():
                results = await retry_async(
                    lambda: asyncio.wait_for(
                        AzureSearchService._search_async(
                            client,
                            search_text=search_text_query,
                            vector_queries=[vector_query],
                            filter=acl_filter,
                            top=10,
                        ),
                        timeout=settings.AZURE_SEARCH_REQUEST_TIMEOUT_SECONDS,
                    ),
                    operation_name="azure_search.top_chunks",
                )

        if not results:
            return []

        top1 = results[0]
        top1_parent_id = top1.get("parent_id")
        top1_title = top1.get("title")
        logger.info(
            "Top chunk document: %s | parent_id: %s",
            top1_title,
            top1_parent_id,
        )
        escaped_parent_id = AzureSearchService._escape_odata_value(
            str(top1_parent_id)
        )

        with timed("retrieval.document_chunks"):
            async with capacity_manager.search_slot():
                full_doc_chunks = await retry_async(
                    lambda: asyncio.wait_for(
                        AzureSearchService._search_async(
                            client,
                            search_text="*",
                            filter=(
                                f"(parent_id eq '{escaped_parent_id}') "
                                f"and ({acl_filter})"
                            ),
                            top=1000,
                        ),
                        timeout=settings.AZURE_SEARCH_REQUEST_TIMEOUT_SECONDS,
                    ),
                    operation_name="azure_search.document_chunks",
                )

        return [
            {
                "score": doc.get("@search.score"),
                "chunk_id": doc.get("chunk_id"),
                "parent_id": doc.get("parent_id"),
                "title": doc.get("title"),
                "content": doc.get("chunk"),
                "source_file": doc.get("source_file"),
                "department": doc.get("department"),
                "owner_role": doc.get("owner_role"),
                "security_level": doc.get("security_level"),
                "document_type": doc.get("document_type"),
                "sensitivity": doc.get("sensitivity"),
                "source_url": doc.get("source_url"),
                "drive_id": doc.get("drive_id"),
                "drive_item_id": doc.get("drive_item_id"),
            }
            for doc in full_doc_chunks
        ]

    @staticmethod
    def retrieve_contract_policy(
        question: str,
        top_k: int,
    ):

        if not question.strip():
            return []

        client = SyncSearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name=settings.AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(
                settings.AZURE_SEARCH_KEY
            ),
        )

        openai_client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )

        embedding_response = (
            openai_client
            .embeddings
            .create(
                model=(
                    settings
                    .AZURE_OPENAI_EMBEDDING_DEPLOYMENT
                ),
                input=question,
            )
        )

        vector_query = VectorizedQuery(
            vector=(
                embedding_response
                .data[0]
                .embedding
            ),
            k_nearest_neighbors=top_k,
            fields="text_vector",
        )

        results = client.search(
            search_text=question,
            vector_queries=[
                vector_query,
            ],
            filter=(
                "document_type eq 'CONTRACT_POLICY'"
            ),
            top=top_k,
        )

        return [
            {
                "score": doc.get("@search.score"),
                "chunk_id": doc.get("chunk_id"),
                "parent_id": doc.get("parent_id"),
                "title": doc.get("title"),
                "content": doc.get("chunk"),
                "source_file": doc.get("source_file"),
                "document_type": doc.get("document_type"),
                "source_url": doc.get("source_url"),
            }
            for doc in results
        ]

    @staticmethod
    async def retrieve_helpdesk(
        question: str,
        top_k: int,
        group_ids: list[str],
        permissions: list[dict],
    ):
        openai_client = AzureSearchService._get_embedding_client()
        acl_filter = AzureSearchService.build_acl_filter(
            group_ids=group_ids,
            permissions=permissions,
        )
        azure_filter = f"(workspace eq 'HELPDESK') and ({acl_filter})"
        logger.info("Azure Filter: %s", azure_filter)

        async with capacity_manager.embedding_slot():
            embedding_response = await retry_async(
                lambda: asyncio.wait_for(
                    openai_client.embeddings.create(
                        model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                        input=question,
                    ),
                    timeout=settings.AZURE_OPENAI_EMBEDDING_REQUEST_TIMEOUT_SECONDS,
                ),
                operation_name="azure_openai.helpdesk_embedding",
            )

        vector_query = VectorizedQuery(
            vector=embedding_response.data[0].embedding,
            k_nearest_neighbors=top_k,
            fields="text_vector",
        )
        client = AzureSearchService._get_search_client()
        async with capacity_manager.search_slot():
            results = await retry_async(
                lambda: asyncio.wait_for(
                    AzureSearchService._search_async(
                        client,
                        search_text=question,
                        vector_queries=[vector_query],
                        filter=azure_filter,
                        top=20,
                    ),
                    timeout=settings.AZURE_SEARCH_REQUEST_TIMEOUT_SECONDS,
                ),
                operation_name="azure_search.helpdesk",
            )

        return [
            {
                "score": doc.get("@search.score"),
                "chunk_id": doc.get("chunk_id"),
                "parent_id": doc.get("parent_id"),
                "title": doc.get("title"),
                "content": doc.get("chunk"),
                "source_file": doc.get("source_file"),
                "department": doc.get("department"),
                "owner_role": doc.get("owner_role"),
                "security_level": doc.get("security_level"),
                "document_type": doc.get("document_type"),
                "sensitivity": doc.get("sensitivity"),
                "source_url": doc.get("source_url"),
                "drive_id": doc.get("drive_id"),
                "drive_item_id": doc.get("drive_item_id"),
            }
            for doc in results
        ]
