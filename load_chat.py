import argparse
import asyncio
import statistics
import time
from collections import Counter
from uuid import uuid4

import httpx


MODEL_ID = "9e88048c-a6da-4f64-ae0c-cbdaaac33de8"
QUESTION = "Cho tôi thông tin về dự án khu công nghiệp ở Long Thành của KN Holding"


async def call_chat(client: httpx.AsyncClient, url: str, user_number: int):
    # Mỗi request đại diện cho một user khác nhau để đo tải toàn hệ thống.
    conversation_id = str(uuid4())
    payload = {
        "conversation_id": conversation_id,
        "question": QUESTION,
        "microsoft_object_id": f"load-user-{user_number}",
        "group_ids": ["string"],
        "role": "4",
        "model_id": MODEL_ID,
        "mode": "PUBLIC",
    }

    started = time.perf_counter()
    timings = {}
    last_event = None

    try:
        async with client.stream("POST", url, json=payload) as response:
            timings["headers"] = time.perf_counter() - started

            if response.status_code != 200:
                await response.aread()
                return {
                    "trace_id": conversation_id,
                    "status": f"HTTP_{response.status_code}",
                    "timings": timings,
                }

            event_name = None
            data_lines = []

            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    event_name = line[6:].strip()
                elif line.startswith("data:"):
                    data_lines.append(line[5:].strip())
                elif line == "":
                    if event_name:
                        last_event = event_name
                        elapsed = time.perf_counter() - started

                        if event_name == "metadata":
                            timings.setdefault("metadata", elapsed)
                        elif event_name == "answer":
                            timings.setdefault("first_answer", elapsed)
                        elif event_name in {"done", "error"}:
                            timings[event_name] = elapsed
                            return {
                                "trace_id": conversation_id,
                                "status": event_name,
                                "timings": timings,
                                "error": "\n".join(data_lines) if event_name == "error" else None,
                            }

                    event_name = None
                    data_lines = []

            return {"trace_id": conversation_id, "status": f"stream_ended_after_{last_event}", "timings": timings}

    except Exception as exc:
        return {
            "trace_id": conversation_id,
            "status": type(exc).__name__,
            "timings": timings,
            "error": str(exc),
        }


def show_metric(results, name):
    values = sorted(
        item["timings"][name]
        for item in results
        if name in item["timings"]
    )
    if not values:
        print(f"{name}: không có dữ liệu")
        return

    p50 = statistics.median(values)
    p95 = values[min(len(values) - 1, int(0.95 * len(values)))]
    print(f"{name}: p50={p50:.2f}s, p95={p95:.2f}s, max={max(values):.2f}s")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=10)
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/chat/query",
    )
    args = parser.parse_args()

    timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)
    limits = httpx.Limits(
        max_connections=args.users,
        max_keepalive_connections=args.users,
    )

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        batch_started = time.perf_counter()
        results = await asyncio.gather(
            *(call_chat(client, args.url, i) for i in range(args.users))
        )
        batch_duration = time.perf_counter() - batch_started

    print(f"\nUsers: {args.users}")
    print(f"Batch duration: {batch_duration:.2f}s")
    print("Statuses:", dict(Counter(item["status"] for item in results)))

    for metric in ("headers", "metadata", "first_answer", "done"):
        show_metric(results, metric)

    print("\nSlowest requests (match trace_id with server [llm_timing]):")
    for item in sorted(
        (result for result in results if "done" in result["timings"]),
        key=lambda result: result["timings"]["done"],
        reverse=True,
    )[:5]:
        timings = item["timings"]
        print(
            f"trace_id={item['trace_id']} status={item['status']} "
            f"first_answer={timings.get('first_answer', 0):.2f}s "
            f"done={timings.get('done', 0):.2f}s"
        )

    errors = [
        item for item in results
        if item["status"] != "done"
    ]
    for item in errors[:5]:
        print("Error sample:", item)


if __name__ == "__main__":
    asyncio.run(main())
