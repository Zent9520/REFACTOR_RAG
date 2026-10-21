import asyncio
import logging
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from time import monotonic, perf_counter

from backend.app.core.settings import settings
from backend.app.shared.resilience.exceptions import (
    DependencyQueueTimeoutError,
    PipelineCapacityExceededError,
    TokenBudgetExceededError,
    UserCapacityExceededError,
)


logger = logging.getLogger(__name__)


class TimedSemaphore:
    def __init__(self, name: str, limit: int, timeout_seconds: float):
        self.name = name
        self.limit = max(1, int(limit))
        self.timeout_seconds = max(0.001, float(timeout_seconds))
        self._semaphore = asyncio.Semaphore(self.limit)
        self._active = 0
        self._waiting = 0

    @asynccontextmanager
    async def slot(self):
        started_at = perf_counter()
        self._waiting += 1
        try:
            try:
                await asyncio.wait_for(
                    self._semaphore.acquire(),
                    timeout=self.timeout_seconds,
                )
            except TimeoutError as exc:
                raise DependencyQueueTimeoutError(
                    f"Timed out waiting for {self.name} capacity."
                ) from exc
        finally:
            self._waiting -= 1

        queue_wait = perf_counter() - started_at
        self._active += 1
        logger.info(
            "[capacity] dependency=%s queue_wait=%.3fs active=%d/%d waiting=%d",
            self.name,
            queue_wait,
            self._active,
            self.limit,
            self._waiting,
        )

        try:
            yield queue_wait
        finally:
            self._active -= 1
            self._semaphore.release()
            logger.info(
                "[capacity] dependency=%s released active=%d/%d waiting=%d",
                self.name,
                self._active,
                self.limit,
                self._waiting,
            )


class OpenAIQuotaBudget:
    """Single-process token bucket for one Azure OpenAI deployment pool."""

    WINDOW_SECONDS = 60.0

    def __init__(
        self,
        requests_per_minute: int,
        tokens_per_minute: int,
        safety_ratio: float,
        timeout_seconds: float,
    ):
        ratio = min(1.0, max(0.1, float(safety_ratio)))
        self.request_capacity = max(1.0, requests_per_minute * ratio)
        self.token_capacity = max(1.0, tokens_per_minute * ratio)
        self.timeout_seconds = max(0.001, float(timeout_seconds))
        self._requests = self.request_capacity
        self._tokens = self.token_capacity
        self._updated_at = monotonic()
        self._lock = asyncio.Lock()

    def _refill(self, now: float) -> None:
        elapsed = max(0.0, now - self._updated_at)
        self._updated_at = now
        self._requests = min(
            self.request_capacity,
            self._requests + elapsed * self.request_capacity / self.WINDOW_SECONDS,
        )
        self._tokens = min(
            self.token_capacity,
            self._tokens + elapsed * self.token_capacity / self.WINDOW_SECONDS,
        )

    async def reserve(self, estimated_tokens: int) -> float:
        token_cost = max(1, int(estimated_tokens))
        if token_cost > self.token_capacity:
            raise TokenBudgetExceededError(
                f"Request needs {token_cost} tokens but the safe TPM capacity is "
                f"{int(self.token_capacity)}."
            )

        started_at = monotonic()
        deadline = started_at + self.timeout_seconds

        while True:
            async with self._lock:
                now = monotonic()
                self._refill(now)

                if self._requests >= 1.0 and self._tokens >= token_cost:
                    self._requests -= 1.0
                    self._tokens -= token_cost
                    waited = now - started_at
                    logger.info(
                        "[capacity] dependency=azure_openai_quota "
                        "queue_wait=%.3fs reserved_tokens=%d "
                        "remaining_tokens=%d remaining_requests=%.1f",
                        waited,
                        token_cost,
                        int(self._tokens),
                        self._requests,
                    )
                    return waited

                request_wait = (
                    max(0.0, 1.0 - self._requests)
                    * self.WINDOW_SECONDS
                    / self.request_capacity
                )
                token_wait = (
                    max(0.0, token_cost - self._tokens)
                    * self.WINDOW_SECONDS
                    / self.token_capacity
                )
                sleep_seconds = max(0.05, request_wait, token_wait)

            remaining = deadline - monotonic()
            if remaining <= 0:
                raise DependencyQueueTimeoutError(
                    "Timed out waiting for Azure OpenAI RPM/TPM capacity."
                )
            await asyncio.sleep(min(sleep_seconds, remaining, 1.0))


@dataclass
class AdmissionPermit:
    manager: "CapacityManager"
    user_id: str
    released: bool = False

    async def release(self) -> None:
        if self.released:
            return
        self.released = True
        await self.manager._release_admission(self.user_id)


class CapacityManager:
    def __init__(self):
        self._pipeline_limit = max(1, settings.RAG_MAX_IN_FLIGHT_REQUESTS)
        self._pipeline = asyncio.Semaphore(self._pipeline_limit)
        self._admission_lock = asyncio.Lock()
        self._user_active: dict[str, int] = {}
        self._user_request_times: dict[str, deque[float]] = {}
        self._pipeline_active = 0

        self.search = TimedSemaphore(
            "azure_search",
            settings.AZURE_SEARCH_MAX_CONCURRENCY,
            settings.AZURE_SEARCH_QUEUE_TIMEOUT_SECONDS,
        )
        self.llm = TimedSemaphore(
            "azure_openai_chat",
            settings.AZURE_OPENAI_CHAT_MAX_CONCURRENCY,
            settings.AZURE_OPENAI_CHAT_QUEUE_TIMEOUT_SECONDS,
        )
        self.embedding = TimedSemaphore(
            "azure_openai_embedding",
            settings.AZURE_OPENAI_EMBEDDING_MAX_CONCURRENCY,
            settings.AZURE_OPENAI_EMBEDDING_QUEUE_TIMEOUT_SECONDS,
        )
        self.openai_quota = OpenAIQuotaBudget(
            requests_per_minute=settings.AZURE_OPENAI_RPM_LIMIT,
            tokens_per_minute=settings.AZURE_OPENAI_TPM_LIMIT,
            safety_ratio=settings.AZURE_OPENAI_QUOTA_SAFETY_RATIO,
            timeout_seconds=settings.AZURE_OPENAI_QUOTA_QUEUE_TIMEOUT_SECONDS,
        )

    async def acquire_admission(self, user_id: str) -> AdmissionPermit:
        normalized_user_id = str(user_id or "anonymous").strip() or "anonymous"
        try:
            await asyncio.wait_for(
                self._pipeline.acquire(),
                timeout=settings.RAG_ADMISSION_TIMEOUT_SECONDS,
            )
        except TimeoutError as exc:
            raise PipelineCapacityExceededError(
                "The RAG pipeline is at capacity."
            ) from exc

        try:
            async with self._admission_lock:
                now = monotonic()
                request_times = self._user_request_times.setdefault(
                    normalized_user_id,
                    deque(),
                )
                while request_times and now - request_times[0] >= 60.0:
                    request_times.popleft()

                if (
                    len(request_times)
                    >= settings.RAG_USER_REQUESTS_PER_MINUTE
                ):
                    raise UserCapacityExceededError(
                        "The user exceeded the per-minute request limit."
                    )

                user_active = self._user_active.get(normalized_user_id, 0)
                if user_active >= settings.RAG_USER_MAX_CONCURRENCY:
                    raise UserCapacityExceededError(
                        "The user has too many active requests."
                    )

                request_times.append(now)
                self._user_active[normalized_user_id] = user_active + 1
                self._pipeline_active += 1
                logger.info(
                    "[capacity] admission user=%s user_active=%d/%d "
                    "pipeline_active=%d/%d",
                    normalized_user_id,
                    user_active + 1,
                    settings.RAG_USER_MAX_CONCURRENCY,
                    self._pipeline_active,
                    self._pipeline_limit,
                )
        except Exception:
            self._pipeline.release()
            raise

        return AdmissionPermit(self, normalized_user_id)

    async def _release_admission(self, user_id: str) -> None:
        async with self._admission_lock:
            active = self._user_active.get(user_id, 0)
            if active <= 1:
                self._user_active.pop(user_id, None)
            else:
                self._user_active[user_id] = active - 1
            self._pipeline_active = max(0, self._pipeline_active - 1)
            logger.info(
                "[capacity] admission_released user=%s pipeline_active=%d/%d",
                user_id,
                self._pipeline_active,
                self._pipeline_limit,
            )
        self._pipeline.release()

    @asynccontextmanager
    async def search_slot(self):
        async with self.search.slot() as queue_wait:
            yield queue_wait

    @asynccontextmanager
    async def embedding_slot(self):
        async with self.embedding.slot() as queue_wait:
            yield queue_wait

    @asynccontextmanager
    async def llm_slot(self, estimated_tokens: int):
        quota_wait = await self.openai_quota.reserve(estimated_tokens)
        async with self.llm.slot() as concurrency_wait:
            yield quota_wait + concurrency_wait


capacity_manager = CapacityManager()
