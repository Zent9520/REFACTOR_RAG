import unittest
from unittest.mock import AsyncMock, patch

from backend.app.core.settings import settings
from backend.app.shared.resilience.exceptions import DependencyUnavailableError
from backend.app.shared.resilience.retry_policy import retry_async


class FakeResponse:
    def __init__(self, headers=None):
        self.headers = headers or {}


class FakeRateLimitError(Exception):
    status_code = 429

    def __init__(self, retry_after_ms="10"):
        super().__init__("rate limited")
        self.response = FakeResponse({"retry-after-ms": retry_after_ms})


class RetryPolicyTest(unittest.IsolatedAsyncioTestCase):

    async def test_retries_429_and_returns_success(self):
        calls = 0

        async def operation():
            nonlocal calls
            calls += 1
            if calls == 1:
                raise FakeRateLimitError()
            return "ok"

        with (
            patch.object(settings, "AZURE_RETRY_MAX_ATTEMPTS", 3),
            patch.object(settings, "AZURE_RETRY_BASE_DELAY_SECONDS", 0.01),
            patch.object(settings, "AZURE_RETRY_MAX_DELAY_SECONDS", 0.02),
            patch.object(settings, "AZURE_RETRY_JITTER_SECONDS", 0.0),
            patch(
                "backend.app.shared.resilience.retry_policy.asyncio.sleep",
                new=AsyncMock(),
            ) as sleep,
        ):
            result = await retry_async(operation, "test.azure")

        print(f"[TEST][RETRY] calls={calls}; result={result}")
        self.assertEqual(result, "ok")
        self.assertEqual(calls, 2)
        sleep.assert_awaited_once()

    async def test_maps_exhausted_429_to_dependency_error(self):
        calls = 0

        async def operation():
            nonlocal calls
            calls += 1
            raise FakeRateLimitError()

        with (
            patch.object(settings, "AZURE_RETRY_MAX_ATTEMPTS", 2),
            patch.object(settings, "AZURE_RETRY_BASE_DELAY_SECONDS", 0.01),
            patch.object(settings, "AZURE_RETRY_MAX_DELAY_SECONDS", 0.02),
            patch.object(settings, "AZURE_RETRY_JITTER_SECONDS", 0.0),
            patch(
                "backend.app.shared.resilience.retry_policy.asyncio.sleep",
                new=AsyncMock(),
            ),
        ):
            with self.assertRaises(DependencyUnavailableError):
                await retry_async(operation, "test.azure")

        print(f"[TEST][RETRY] exhausted after calls={calls}; mapped safely")
        self.assertEqual(calls, 2)
