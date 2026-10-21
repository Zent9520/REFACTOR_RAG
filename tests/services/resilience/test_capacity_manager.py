import asyncio
import unittest
from unittest.mock import patch

from backend.app.core.settings import settings
from backend.app.shared.resilience.capacity_manager import (
    CapacityManager,
    OpenAIQuotaBudget,
    TimedSemaphore,
)
from backend.app.shared.resilience.exceptions import (
    DependencyQueueTimeoutError,
    PipelineCapacityExceededError,
    UserCapacityExceededError,
)


class CapacityManagerTest(unittest.IsolatedAsyncioTestCase):

    async def test_accepts_100_concurrent_requests_and_rejects_101st(self):
        with (
            patch.object(settings, "RAG_MAX_IN_FLIGHT_REQUESTS", 100),
            patch.object(settings, "RAG_USER_MAX_CONCURRENCY", 1),
            patch.object(settings, "RAG_USER_REQUESTS_PER_MINUTE", 10),
            patch.object(settings, "RAG_ADMISSION_TIMEOUT_SECONDS", 0.01),
        ):
            manager = CapacityManager()
            permits = await asyncio.gather(*(
                manager.acquire_admission(f"user-{index}")
                for index in range(100)
            ))

            try:
                self.assertEqual(len(permits), 100)
                self.assertEqual(manager._pipeline_active, 100)
                self.assertEqual(len(manager._user_active), 100)
                print(
                    "[TEST][ADMISSION_100] accepted=100 active=100/100; "
                    "request=101 must be rejected"
                )

                with self.assertRaises(PipelineCapacityExceededError):
                    await manager.acquire_admission("user-101")
            finally:
                await asyncio.gather(*(
                    permit.release()
                    for permit in permits
                ))

            self.assertEqual(manager._pipeline_active, 0)
            self.assertEqual(manager._user_active, {})
            print(
                "[TEST][ADMISSION_100] released=100 active=0/100; "
                "no permit leaked"
            )

    async def test_rejects_third_concurrent_request_for_same_user(self):
        with (
            patch.object(settings, "RAG_MAX_IN_FLIGHT_REQUESTS", 10),
            patch.object(settings, "RAG_USER_MAX_CONCURRENCY", 2),
            patch.object(settings, "RAG_USER_REQUESTS_PER_MINUTE", 10),
            patch.object(settings, "RAG_ADMISSION_TIMEOUT_SECONDS", 0.02),
        ):
            manager = CapacityManager()
            first = await manager.acquire_admission("user-1")
            second = await manager.acquire_admission("user-1")

            print("[TEST][ADMISSION] user-1 active=2/2; third request rejected")
            with self.assertRaises(UserCapacityExceededError):
                await manager.acquire_admission("user-1")

            await first.release()
            await second.release()
            self.assertEqual(manager._pipeline_active, 0)
            print("[TEST][ADMISSION] all permits released; pipeline_active=0")

    async def test_rejects_request_when_pipeline_is_full(self):
        with (
            patch.object(settings, "RAG_MAX_IN_FLIGHT_REQUESTS", 1),
            patch.object(settings, "RAG_USER_MAX_CONCURRENCY", 2),
            patch.object(settings, "RAG_USER_REQUESTS_PER_MINUTE", 10),
            patch.object(settings, "RAG_ADMISSION_TIMEOUT_SECONDS", 0.01),
        ):
            manager = CapacityManager()
            permit = await manager.acquire_admission("user-1")

            print("[TEST][ADMISSION] pipeline active=1/1; next request rejected")
            with self.assertRaises(PipelineCapacityExceededError):
                await manager.acquire_admission("user-2")

            await permit.release()

    async def test_enforces_per_user_requests_per_minute(self):
        with (
            patch.object(settings, "RAG_MAX_IN_FLIGHT_REQUESTS", 10),
            patch.object(settings, "RAG_USER_MAX_CONCURRENCY", 2),
            patch.object(settings, "RAG_USER_REQUESTS_PER_MINUTE", 1),
            patch.object(settings, "RAG_ADMISSION_TIMEOUT_SECONDS", 0.02),
        ):
            manager = CapacityManager()
            permit = await manager.acquire_admission("user-1")
            await permit.release()

            print("[TEST][RATE] user-1 used 1/1 request in current minute")
            with self.assertRaises(UserCapacityExceededError):
                await manager.acquire_admission("user-1")

    async def test_timed_semaphore_times_out_and_recovers(self):
        limiter = TimedSemaphore(
            name="test_dependency",
            limit=1,
            timeout_seconds=0.01,
        )

        async with limiter.slot():
            print("[TEST][SEMAPHORE] active=1/1; nested request waiting")
            with self.assertRaises(DependencyQueueTimeoutError):
                async with limiter.slot():
                    self.fail("Nested slot must not be acquired")

        async with limiter.slot():
            print("[TEST][SEMAPHORE] permit released and acquired again")

        self.assertEqual(limiter._active, 0)

    async def test_token_budget_times_out_when_quota_is_exhausted(self):
        budget = OpenAIQuotaBudget(
            requests_per_minute=1,
            tokens_per_minute=100,
            safety_ratio=1.0,
            timeout_seconds=0.01,
        )
        await budget.reserve(80)

        print("[TEST][TOKEN] reserved=80; remaining budget is insufficient")
        with self.assertRaises(DependencyQueueTimeoutError):
            await budget.reserve(80)
