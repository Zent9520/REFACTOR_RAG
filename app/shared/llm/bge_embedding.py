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

from backend.app.core.settings import settings


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
        """Return one BGE embedding for a retrieval query."""

        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed several retrieval queries while preserving input order.

        The endpoint must return one vector for every input text.  A count
        mismatch is rejected instead of guessing, because callers use the
        vector position to map legal results back to the correct contract
        check.
        """

        if not texts:
            raise ValueError("BGE embedding batch must not be empty.")

        request_texts: list[str] = []
        for text in texts:
            if not isinstance(text, str) or not text.strip():
                raise ValueError(
                    "Every BGE embedding batch item must be a non-empty string."
                )
            request_texts.append(f"{self.query_prefix}{text.strip()}")

        if self.endpoint:
            vectors = self._embed_http_batch(request_texts)
        elif self.local_model_path:
            vectors = self._embed_local_batch(request_texts)
        else:
            raise RuntimeError(
                "BGE is not configured. Set BGE_EMBEDDING_ENDPOINT (HTTP "
                "mode) or BGE_LOCAL_MODEL_PATH (local model mode)."
            )

        if len(vectors) != len(request_texts):
            raise RuntimeError(
                "BGE embedding count mismatch: "
                f"sent {len(request_texts)} texts but received "
                f"{len(vectors)} vectors."
            )

        if settings.BGE_NORMALIZE_EMBEDDINGS:
            vectors = [self._normalize(vector) for vector in vectors]
        return vectors

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
        return self._embed_local_batch([text])[0]

    def _embed_local_batch(self, texts: list[str]) -> list[list[float]]:
        model = self._get_local_model(self.local_model_path)
        with self._encode_lock:
            output = model.encode(
                texts,
                batch_size=len(texts),
                max_length=self.LOCAL_MAX_LENGTH,
                return_dense=True,
                return_sparse=False,
                return_colbert_vecs=False,
            )
        return [
            [float(value) for value in vector]
            for vector in output["dense_vecs"]
        ]

    # ------------------------------------------------------------------
    # HTTP endpoint mode
    # ------------------------------------------------------------------
    def _embed_http(self, text: str) -> list[float]:
        return self._embed_http_batch([text])[0]

    def _embed_http_batch(self, texts: list[str]) -> list[list[float]]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = self._build_payload(texts)
        with httpx.Client(timeout=self.DEFAULT_TIMEOUT_SECONDS) as client:
            response = client.post(
                self.endpoint,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

        return self._extract_vectors(
            response.json(),
            expected_count=len(texts),
        )

    def _build_payload(self, texts: list[str]) -> dict[str, Any]:
        if self.request_format == "openai":
            return {"model": self.model, "input": texts}
        if self.request_format == "huggingface":
            return {"inputs": texts}
        raise ValueError(
            "BGE_EMBEDDING_REQUEST_FORMAT must be 'openai' or 'huggingface'."
        )

    @classmethod
    def _extract_vector(cls, payload: Any) -> list[float]:
        return cls._extract_vectors(payload, expected_count=1)[0]

    @classmethod
    def _extract_vectors(
        cls,
        payload: Any,
        expected_count: int,
    ) -> list[list[float]]:
        candidates: Any = None

        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, list) and data and all(
                isinstance(item, dict) for item in data
            ):
                if all(isinstance(item.get("index"), int) for item in data):
                    data = sorted(data, key=lambda item: item["index"])
                candidates = [item.get("embedding") for item in data]
            elif isinstance(payload.get("embeddings"), list):
                candidates = payload["embeddings"]
            elif payload.get("embedding") is not None:
                candidates = [payload["embedding"]]
        elif isinstance(payload, list):
            candidates = payload

        if not isinstance(candidates, list):
            raise RuntimeError(
                "BGE endpoint response does not contain embedding vectors. "
                "Update BGEEmbeddingService._extract_vectors for its response schema."
            )

        # Keep compatibility with endpoints that return one flat vector for a
        # one-item batch.
        if expected_count == 1 and candidates and all(
            isinstance(value, int | float) for value in candidates
        ):
            candidates = [candidates]

        vectors: list[list[float]] = []
        for candidate in candidates:
            if not isinstance(candidate, list) or not candidate or not all(
                isinstance(value, int | float) for value in candidate
            ):
                raise RuntimeError(
                    "BGE endpoint response contains an invalid embedding vector."
                )
            vectors.append([float(value) for value in candidate])

        if len(vectors) != expected_count:
            raise RuntimeError(
                "BGE endpoint embedding count mismatch: "
                f"expected {expected_count}, received {len(vectors)}."
            )
        return vectors

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            raise RuntimeError("BGE returned a zero embedding vector.")
        return [value / magnitude for value in vector]
