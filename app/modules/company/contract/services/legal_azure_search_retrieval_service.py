"""Vector retrieval for legal sources used by contract legal review.

The legal Azure AI Search index stores vectors in the ``embedding`` field
(1024 dimensions).  The analyzer produces up to two legal retrieval seeds for
each contract check; BGE embeds each seed independently and Azure AI Search
queries that field.  The best unique hits from both searches become the legal
context for the reviewer model.

The supplied legal index schema does not expose a legal-body/content field.
``vn_text`` below therefore contains only the retrievable legal metadata and
citations.  Add a retrievable provision/body field to the index if the
reviewer must quote or reason over the actual text of a legal article.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from backend.app.core.settings import settings
from backend.app.shared.llm.bge_embedding import BGEEmbeddingService


class LegalAzureSearchRetrievalService:
    """Retrieve legal references from the dedicated Azure AI Search index."""

    # The analyzer output may contain more fields, but the current legal-review
    # contract calls for two legal-document seeds per contract check.
    MAX_SEEDS = 2
    TOP_K = 4
    EMBEDDING_DIMENSIONS = 1024

    # The main document RAG index uses ``text_vector``.  The legal index uses
    # the distinct field supplied by the Azure team.
    VECTOR_FIELD = "embedding"

    RETRIEVABLE_FIELDS = (
        "id",
        "document_id",
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
        "issue_date",
        "effective_date",
        "status",
        "update_date",
        "signer",
        "issuing_body",
        "parent_acts",
        "article_titles",
        "citations",
        "url",
    )

    METADATA_FIELDS = tuple(
        field for field in RETRIEVABLE_FIELDS
        if field not in {"id", "document_id"}
    )

    @classmethod
    def retrieve(cls, metadata_seeds: Any) -> list[dict[str, Any]]:
        """Embed up to two analyzer seeds and return the best unique laws.

        The method is synchronous because the Azure SDK clients used here are
        synchronous.  ``LegalContractAnalysisService`` invokes it through
        ``asyncio.to_thread`` so an SSE request does not block the event loop.
        """

        seeds = cls._extract_seeds(metadata_seeds)
        if not seeds:
            raise ValueError("Legal vector retrieval requires one or two seeds.")

        index_name = settings.AZURE_SEARCH_CONTRACT_NAME.strip()
        if not index_name:
            raise RuntimeError(
                "AZURE_SEARCH_CONTRACT_NAME is required for legal vector retrieval."
            )

        search_client = SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name=index_name,
            credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY),
        )
        embedding_service = BGEEmbeddingService()

        candidates: dict[str, dict[str, Any]] = {}
        for seed in seeds:
            vector = cls._embed_seed(embedding_service, seed)
            vector_query = VectorizedQuery(
                vector=vector,
                k_nearest_neighbors=cls.TOP_K,
                fields=cls.VECTOR_FIELD,
            )
            results = search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                select=", ".join(cls.RETRIEVABLE_FIELDS),
                top=cls.TOP_K,
            )

            for document in results:
                item = cls._to_context(document, seed)
                # ``id`` is the Azure index key, so it is the correct identity
                # when a law has several distinct indexed records.
                key = str(item["index_id"])
                existing = candidates.get(key)
                if existing is None or item["score"] > existing["score"]:
                    candidates[key] = item

        return sorted(
            candidates.values(),
            key=lambda item: item["score"],
            reverse=True,
        )[:cls.TOP_K]

    @classmethod
    def _embed_seed(
        cls,
        embedding_service: BGEEmbeddingService,
        seed: str,
    ) -> list[float]:
        embedding = embedding_service.embed(seed)
        if len(embedding) != cls.EMBEDDING_DIMENSIONS:
            raise RuntimeError(
                "Legal embedding dimension mismatch: the legal index requires "
                f"{cls.EMBEDDING_DIMENSIONS}, but BGE returned "
                f"{len(embedding)}. Use the same 1024-dimension BGE model "
                "that embedded the legal Azure Index."
            )
        return embedding

    @classmethod
    def _extract_seeds(cls, raw_seeds: Any) -> list[str]:
        """Keep the first two distinct, non-empty seed strings in analyzer order."""

        values: Iterable[Any]
        if isinstance(raw_seeds, dict):
            # Accept both the current ``metadata_seeds`` map and a future
            # explicit ``{"seeds": [seed_1, seed_2]}`` analyzer payload.
            if isinstance(raw_seeds.get("seeds"), list):
                values = raw_seeds["seeds"]
            else:
                values = (
                    value
                    for seed_values in raw_seeds.values()
                    if isinstance(seed_values, list)
                    for value in seed_values
                )
        elif isinstance(raw_seeds, list):
            values = raw_seeds
        else:
            return []

        seeds: list[str] = []
        seen: set[str] = set()
        for value in values:
            if not isinstance(value, str):
                continue
            seed = value.strip()
            normalized = seed.casefold()
            if not seed or normalized in seen:
                continue
            seen.add(normalized)
            seeds.append(seed)
            if len(seeds) == cls.MAX_SEEDS:
                break
        return seeds

    @classmethod
    def _to_context(cls, document: Any, matched_seed: str) -> dict[str, Any]:
        metadata = {
            field: cls._json_value(document.get(field))
            for field in cls.METADATA_FIELDS
            if document.get(field) not in (None, "", [])
        }
        return {
            # Keep the old retrieval contract so the existing reviewer prompt
            # and response validator can continue consuming ``vn_text``.
            "document_id": str(document.get("document_id") or document.get("id")),
            "index_id": str(document.get("id")),
            "metadata": metadata,
            "vn_text": cls._metadata_as_context(metadata),
            "score": float(document.get("@search.score") or 0.0),
            "matched_seed": matched_seed,
        }

    @staticmethod
    def _json_value(value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, list):
            return [LegalAzureSearchRetrievalService._json_value(item) for item in value]
        return value

    @staticmethod
    def _metadata_as_context(metadata: dict[str, Any]) -> str:
        """Serialize only data that the supplied index marks retrievable."""

        if not metadata:
            return ""
        lines = []
        for key, value in metadata.items():
            if isinstance(value, list):
                value = "; ".join(str(item) for item in value)
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
