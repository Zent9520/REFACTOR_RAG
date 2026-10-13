from azure.search.documents import (
    SearchClient
)

from azure.search.documents.models import (
    VectorizedQuery
)

from azure.core.credentials import (
    AzureKeyCredential
)

from openai import (
    AzureOpenAI
)

from app.core.settings import settings

from backend.app.modules.configuration.repositories.rag_config_repository import (
    WorkspaceConfigRepository
)
from backend.app.modules.configuration.enums.prompt_code import PromptCode

from backend.app.shared.llm.azure_openai_service import AzureOpenAIService
import json


class AzureSearchService:

    @staticmethod
    def _escape_odata_value(value: str) -> str:

        return value.replace("'", "''")

    @staticmethod
    def build_acl_filter(
        user_object_id: str,
        group_ids: list[str],
    ) -> str:

        user_object_id = user_object_id.strip()

        if not user_object_id:
            raise ValueError("user_object_id must not be empty.")

        escaped_user_id = (
            AzureSearchService
            ._escape_odata_value(user_object_id)
        )
        filters = [
            "allowed_user_ids/any("
            f"u: u eq '{escaped_user_id}'"
            ")"
        ]
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

        if normalized_group_ids:
            group_filter = " or ".join(
                f"g eq '{group_id}'"
                for group_id in normalized_group_ids
            )
            filters.append(
                "allowed_group_ids/any("
                f"g: {group_filter}"
                ")"
            )

        return " or ".join(filters)
    
    
    
    
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

        print("Rewritten search query:", result)

        search_text_query = result.strip() if result else question

        return search_text_query


   
    @staticmethod
    async def retrieve(
        question: str,
        user_object_id: str,
        group_ids: list[str],
    ):

        client = SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name=settings.AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY),
        )

        acl_filter = AzureSearchService.build_acl_filter(
            user_object_id=user_object_id,
            group_ids=group_ids,
        )

        search_text_query = await AzureSearchService.analyze_question_to_query(question)

        openai_client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )

        embedding_response = openai_client.embeddings.create(
            model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            input=question,
        )
        query_embedding = embedding_response.data[0].embedding

        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=10,
            fields="text_vector",
        )

        results = list(client.search(
            search_text=search_text_query,
            vector_queries=[vector_query],
            filter=acl_filter,
            top=10,
        ))

        if not results:
            return []

        top1 = results[0]
        top1_parent_id = top1.get("parent_id")
        top1_title = top1.get("title")

        print("Top1 chunk thuộc document:", top1_title, "| parent_id:", top1_parent_id)

        escaped_parent_id = AzureSearchService._escape_odata_value(
            str(top1_parent_id)
        )
        full_doc_chunks = list(client.search(
            search_text="*",
            filter=(
                f"(parent_id eq '{escaped_parent_id}') "
                f"and ({acl_filter})"
            ),
            top=1000,
        ))

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

        client = SearchClient(
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
    def retrieve_helpdesk(
        question: str,
        top_k: int,
        user_object_id: str,
        group_ids: list[str],
    ):

        client = SearchClient(

            endpoint=
            settings
            .AZURE_SEARCH_ENDPOINT,

            index_name=
            settings
            .AZURE_SEARCH_INDEX,

            credential=
            AzureKeyCredential(

                settings
                .AZURE_SEARCH_KEY

            )

        )

        openai_client = AzureOpenAI(

            api_key=
            settings
            .AZURE_OPENAI_API_KEY,

            azure_endpoint=
            settings
            .AZURE_OPENAI_ENDPOINT,

            api_version=
            settings
            .AZURE_OPENAI_API_VERSION,

        )

        embedding_response = (

            openai_client
            .embeddings
            .create(

                model=
                settings
                .AZURE_OPENAI_EMBEDDING_DEPLOYMENT,

                input=
                question,

            )

        )

        query_embedding = (

            embedding_response
            .data[0]
            .embedding

        )

        vector_query = (

            VectorizedQuery(

                vector=
                query_embedding,

                k_nearest_neighbors=
                top_k,

                fields=
                "text_vector",

            )

        )

        acl_filter = AzureSearchService.build_acl_filter(
            user_object_id=user_object_id,
            group_ids=group_ids,
        )
        azure_filter = (
            "(workspace eq 'HELPDESK') "
            f"and ({acl_filter})"
        )

        print(
            "Azure Filter:",
            azure_filter,
        )

        results = client.search(

            search_text=
            question,

            vector_queries=[
                vector_query,
            ],

            filter=
            azure_filter,

            top=
            20,

        )

        return [

            {

                "score":
                doc.get("@search.score"),

                "chunk_id":
                doc.get("chunk_id"),

                "parent_id":
                doc.get("parent_id"),

                "title":
                doc.get("title"),

                "content":
                doc.get("chunk"),

                "source_file":
                doc.get("source_file"),

                "department":
                doc.get("department"),

                "owner_role":
                doc.get("owner_role"),

                "security_level":
                doc.get("security_level"),

                "document_type":
                doc.get("document_type"),

                "sensitivity":
                doc.get("sensitivity"),
                "source_url":
                doc.get("source_url"),

                "drive_id":
                doc.get("drive_id"),

                "drive_item_id":
                doc.get("drive_item_id"),

            }

            for doc in results

        ]
