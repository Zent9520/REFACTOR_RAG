"""BGE embedding adapter.

Two modes, chosen by configuration:

* HTTP endpoint: used when ``BGE_EMBEDDING_ENDPOINT`` is set.
    - ``openai``: ``POST {endpoint}`` with ``{"model": ..., "input": ...}``
      and response ``{"data": [{"embedding": [...]}]}``.
    - ``huggingface``: ``POST {endpoint}`` with ``{"inputs": ...}`` and
      response ``[[...]]`` (or ``{"embedding": [...]}``).
* Local model: used when no endpoint is set but ``BGE_LOCAL_MODEL_PATH``
  points to a downloaded BAAI/bge-m3 directory (loaded once per process
  with FlagEmbedding, dense vector only).
"""

from __future__ import annotations

import math
import threading
from typing import Any

import httpx

from app.core.settings import settings


class BGEEmbeddingService:
    """Create query embeddings in the same BGE vector space as the legal index."""

    DEFAULT_TIMEOUT_SECONDS = 30.0
    LOCAL_MAX_LENGTH = 512

    _local_model: Any = None
    _load_lock = threading.Lock()
    _encode_lock = threading.Lock()

    def __init__(self) -> None:
        self.endpoint = (settings.BGE_EMBEDDING_ENDPOINT or "").strip()
        self.api_key = (settings.BGE_EMBEDDING_API_KEY or "").strip()
        self.model = (settings.BGE_EMBEDDING_MODEL or "BAAI/bge-m3").strip()
        self.request_format = (
            settings.BGE_EMBEDDING_REQUEST_FORMAT or "openai"
        ).strip().lower()
        self.query_prefix = settings.BGE_QUERY_PREFIX or ""
        self.local_model_path = (settings.BGE_LOCAL_MODEL_PATH or "").strip()

    def embed(self, text: str) -> list[float]:
        """Return one BGE embedding for a retrieval query.

        The prefix is intentionally configurable.  It must match the query
        instruction, if any, used while building the legal Azure Index.
        """

        if not text or not text.strip():
            raise ValueError("BGE embedding input must not be empty.")

        request_text = f"{self.query_prefix}{text.strip()}"

        if self.endpoint:
            vector = self._embed_http(request_text)
        elif self.local_model_path:
            vector = self._embed_local(request_text)
        else:
            raise RuntimeError(
                "BGE is not configured. Set BGE_EMBEDDING_ENDPOINT (HTTP "
                "mode) or BGE_LOCAL_MODEL_PATH (local model mode)."
            )

        if settings.BGE_NORMALIZE_EMBEDDINGS:
            vector = self._normalize(vector)
        return vector

    @classmethod
    def preload(cls) -> None:
        """Optionally call at app startup so the first request is not slow."""

        path = (settings.BGE_LOCAL_MODEL_PATH or "").strip()
        if path and not (settings.BGE_EMBEDDING_ENDPOINT or "").strip():
            cls._get_local_model(path)

    # ------------------------------------------------------------------
    # Local model mode
    # ------------------------------------------------------------------
    @classmethod
    def _get_local_model(cls, model_path: str) -> Any:
        if cls._local_model is None:
            with cls._load_lock:
                if cls._local_model is None:
                    from FlagEmbedding import BGEM3FlagModel

                    cls._local_model = BGEM3FlagModel(
                        model_path,
                        use_fp16=bool(settings.BGE_USE_FP16),
                    )
        return cls._local_model

    def _embed_local(self, text: str) -> list[float]:
        model = self._get_local_model(self.local_model_path)
        with self._encode_lock:
            output = model.encode(
                [text],
                batch_size=1,
                max_length=self.LOCAL_MAX_LENGTH,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False,
            )
        return [float(value) for value in output["dense_vecs"][0]]

    # ------------------------------------------------------------------
    # HTTP endpoint mode
    # ------------------------------------------------------------------
    def _embed_http(self, text: str) -> list[float]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = self._build_payload(text)
        with httpx.Client(timeout=self.DEFAULT_TIMEOUT_SECONDS) as client:
            response = client.post(
                self.endpoint,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

        return self._extract_vector(response.json())

    def _build_payload(self, text: str) -> dict[str, Any]:
        if self.request_format == "openai":
            return {"model": self.model, "input": text}
        if self.request_format == "huggingface":
            return {"inputs": text}
        raise ValueError(
            "BGE_EMBEDDING_REQUEST_FORMAT must be 'openai' or 'huggingface'."
        )

    @staticmethod
    def _extract_vector(payload: Any) -> list[float]:
        candidate: Any = None

        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, list) and data and isinstance(data[0], dict):
                candidate = data[0].get("embedding")
            if candidate is None:
                candidate = payload.get("embedding")
            if candidate is None:
                embeddings = payload.get("embeddings")
                if isinstance(embeddings, list) and embeddings:
                    candidate = embeddings[0]
        elif isinstance(payload, list) and payload:
            candidate = payload[0]

        # Hugging Face feature-extraction endpoints may return [[float, ...]].
        if isinstance(candidate, list) and candidate and isinstance(candidate[0], list):
            candidate = candidate[0]

        if not isinstance(candidate, list) or not all(
            isinstance(value, int | float) for value in candidate
        ):
            raise RuntimeError(
                "BGE endpoint response does not contain an embedding vector. "
                "Update BGEEmbeddingService._extract_vector for its response schema."
            )

        return [float(value) for value in candidate]

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            raise RuntimeError("BGE returned a zero embedding vector.")
        return [value / magnitude for value in vector]