import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

from azure.core.exceptions import ServiceRequestError, ServiceResponseError
from openai import APIConnectionError, APITimeoutError

from backend.app.core.settings import settings
from backend.app.shared.resilience.exceptions import DependencyUnavailableError


logger = logging.getLogger(__name__)
T = TypeVar("T")


def _status_code(exc: Exception) -> int | None:
    value = getattr(exc, "status_code", None)
    if isinstance(value, int):
        return value
    response = getattr(exc, "response", None)
    value = getattr(response, "status_code", None)
    return value if isinstance(value, int) else None


def _retry_after_seconds(exc: Exception) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if not headers:
        return None

    retry_after_ms = headers.get("retry-after-ms")
    if retry_after_ms:
        try:
            return max(0.0, float(retry_after_ms) / 1000.0)
        except (TypeError, ValueError):
            pass

    retry_after = headers.get("retry-after")
    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except (TypeError, ValueError):
            pass
    return None


def _is_retryable(exc: Exception) -> bool:
    status = _status_code(exc)
    if status == 429 or (status is not None and 500 <= status <= 599):
        return True
    return isinstance(
        exc,
        (
            APIConnectionError,
            APITimeoutError,
            ServiceRequestError,
            ServiceResponseError,
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        ),
    )


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    operation_name: str,
) -> T:
    max_attempts = max(1, settings.AZURE_RETRY_MAX_ATTEMPTS)

    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()
        except Exception as exc:
            retryable = _is_retryable(exc)
            if not retryable:
                raise
            if attempt >= max_attempts:
                raise DependencyUnavailableError(
                    f"{operation_name} remained unavailable after "
                    f"{max_attempts} attempts."
                ) from exc

            retry_after = _retry_after_seconds(exc)
            exponential = min(
                settings.AZURE_RETRY_MAX_DELAY_SECONDS,
                settings.AZURE_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1)),
            )
            delay = retry_after if retry_after is not None else exponential
            delay = min(
                settings.AZURE_RETRY_MAX_DELAY_SECONDS,
                delay + random.uniform(0.0, settings.AZURE_RETRY_JITTER_SECONDS),
            )
            logger.warning(
                "[retry] operation=%s attempt=%d/%d status=%s delay=%.3fs",
                operation_name,
                attempt,
                max_attempts,
                _status_code(exc),
                delay,
            )
            await asyncio.sleep(delay)

    raise RuntimeError("Retry loop exited unexpectedly.")
