"""Operational validation for backend.main.RateLimitMiddleware.

This harness exercises the real middleware dispatch path with:
- thousands of unique clients
- bounded cache growth
- TTL expiry
- burst stability
- basic concurrent behavior

It keeps the workload small, local, and reproducible.
"""

from __future__ import annotations

import asyncio
import gc
import os
import sys
import time
import tracemalloc
from dataclasses import dataclass
from typing import Awaitable, Callable

from fastapi.responses import JSONResponse
from starlette.requests import Request


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


os.environ.setdefault("ENV", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///./backend.db")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("RATE_LIMIT_CACHE_MAXSIZE", "1000")


@dataclass
class PhaseResult:
    name: str
    requests: int
    ok: int
    rate_limited: int
    elapsed_s: float
    avg_latency_ms: float


def build_request(host: str, path: str = "/health") -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": [],
        "client": (host, 12345),
        "server": ("testserver", 80),
    }
    return Request(scope)


def generate_unique_ips(count: int) -> list[str]:
    ips: list[str] = []
    for index in range(count):
        third = (index // 256) % 256
        fourth = index % 256
        ips.append(f"10.0.{third}.{fourth}")
    return ips


def approximate_cache_bytes(store) -> int:
    seen: set[int] = set()

    def walk(value) -> int:
        object_id = id(value)
        if object_id in seen:
            return 0
        seen.add(object_id)

        size = sys.getsizeof(value)

        if isinstance(value, dict):
            for key, item in value.items():
                size += walk(key)
                size += walk(item)
            return size

        if isinstance(value, (list, tuple, set, frozenset)):
            for item in value:
                size += walk(item)
            return size

        try:
            from collections.abc import Mapping

            if isinstance(value, Mapping):
                for key, item in value.items():
                    size += walk(key)
                    size += walk(item)
        except Exception:
            pass

        return size

    return walk(store)


async def invoke_middleware(middleware, host: str) -> tuple[int, float]:
    request = build_request(host)

    async def call_next(_: Request):
        return JSONResponse({"state": "ok"}, status_code=200)

    started = time.perf_counter()
    response = await middleware.dispatch(request, call_next)
    elapsed = time.perf_counter() - started
    return response.status_code, elapsed


async def run_unique_client_burst(middleware) -> dict[str, object]:
    total_clients = 3000
    ips = generate_unique_ips(total_clients)

    first_chunk_latencies: list[float] = []
    last_chunk_latencies: list[float] = []
    rate_limited = 0

    burst_started = time.perf_counter()
    for index, ip in enumerate(ips):
        status_code, latency = await invoke_middleware(middleware, ip)
        if status_code == 429:
            rate_limited += 1

        if index < 500:
            first_chunk_latencies.append(latency)
        if index >= total_clients - 500:
            last_chunk_latencies.append(latency)

    elapsed = time.perf_counter() - burst_started
    cache_size = len(middleware.store)
    cache_bytes = approximate_cache_bytes(middleware.store)

    return {
        "requests": total_clients,
        "ok": total_clients - rate_limited,
        "rate_limited": rate_limited,
        "elapsed_s": elapsed,
        "avg_latency_ms": (elapsed / total_clients) * 1000.0,
        "cache_size": cache_size,
        "cache_bytes": cache_bytes,
        "first_chunk_avg_ms": (sum(first_chunk_latencies) / len(first_chunk_latencies)) * 1000.0,
        "last_chunk_avg_ms": (sum(last_chunk_latencies) / len(last_chunk_latencies)) * 1000.0,
    }


async def run_ttl_eviction_check(middleware, ttl_seconds: float) -> dict[str, object]:
    before_size = len(middleware.store)
    before_bytes = approximate_cache_bytes(middleware.store)

    await asyncio.sleep(ttl_seconds + 0.25)

    started = time.perf_counter()
    status_code, latency = await invoke_middleware(middleware, "10.9.9.9")
    eviction_elapsed = time.perf_counter() - started

    after_size = len(middleware.store)
    after_bytes = approximate_cache_bytes(middleware.store)

    return {
        "before_size": before_size,
        "before_bytes": before_bytes,
        "status_code": status_code,
        "request_latency_s": latency,
        "eviction_elapsed_s": eviction_elapsed,
        "after_size": after_size,
        "after_bytes": after_bytes,
    }


async def run_concurrency_checks(middleware) -> dict[str, object]:
    unique_hosts = generate_unique_ips(200)
    start = time.perf_counter()
    unique_results = await asyncio.gather(*(invoke_middleware(middleware, host) for host in unique_hosts))
    unique_elapsed = time.perf_counter() - start

    concurrent_statuses = [status for status, _ in unique_results]
    unique_latency_avg_ms = (sum(latency for _, latency in unique_results) / len(unique_results)) * 1000.0

    same_ip = "10.250.250.250"
    middleware.max_requests = 5
    same_ip_results = await asyncio.gather(*(invoke_middleware(middleware, same_ip) for _ in range(20)))
    same_ip_ok = sum(1 for status, _ in same_ip_results if status == 200)
    same_ip_rate_limited = sum(1 for status, _ in same_ip_results if status == 429)

    return {
        "unique_elapsed_s": unique_elapsed,
        "unique_latency_avg_ms": unique_latency_avg_ms,
        "unique_statuses": concurrent_statuses,
        "same_ip_ok": same_ip_ok,
        "same_ip_rate_limited": same_ip_rate_limited,
        "same_ip_statuses": [status for status, _ in same_ip_results],
    }


async def main() -> int:
    tracemalloc.start()
    gc.collect()

    from backend.main import RateLimitMiddleware

    class DummyApp:
        pass

    window_seconds = 1.5
    middleware = RateLimitMiddleware(DummyApp(), window_seconds=window_seconds, max_requests=5)

    base_current, base_peak = tracemalloc.get_traced_memory()

    print("=" * 72)
    print("OPERATIONAL VALIDATION: RateLimitMiddleware")
    print("=" * 72)
    print(f"Config: window={window_seconds}s, max_requests=5, cache_maxsize=1000")
    print(f"Baseline traced memory: current={base_current / 1024:.1f} KB, peak={base_peak / 1024:.1f} KB")

    unique = await run_unique_client_burst(middleware)
    peak_current, peak_peak = tracemalloc.get_traced_memory()

    print("\n[PHASE 1] Unique-client burst")
    print(f"  Requests: {unique['requests']}")
    print(f"  Cache size after burst: {unique['cache_size']}")
    print(f"  Approx cache bytes: {unique['cache_bytes'] / 1024:.1f} KB")
    print(f"  Average latency: {unique['avg_latency_ms']:.3f} ms")
    print(f"  First 500 avg: {unique['first_chunk_avg_ms']:.3f} ms")
    print(f"  Last 500 avg: {unique['last_chunk_avg_ms']:.3f} ms")
    print(f"  Traced memory now: current={peak_current / 1024:.1f} KB, peak={peak_peak / 1024:.1f} KB")

    assert unique["cache_size"] <= 1000, f"cache exceeded maxsize: {unique['cache_size']}"
    assert unique["rate_limited"] == 0, "unexpected rate limiting during unique-client burst"
    assert unique["last_chunk_avg_ms"] <= unique["first_chunk_avg_ms"] * 4.0 + 0.5, (
        "latency degraded too quickly during burst"
    )

    ttl = await run_ttl_eviction_check(middleware, window_seconds)
    print("\n[PHASE 2] TTL eviction")
    print(f"  Cache size before TTL trigger: {ttl['before_size']}")
    print(f"  Cache size after TTL trigger: {ttl['after_size']}")
    print(f"  Approx cache bytes before/after: {ttl['before_bytes'] / 1024:.1f} KB -> {ttl['after_bytes'] / 1024:.1f} KB")
    print(f"  Eviction-trigger request latency: {ttl['request_latency_s'] * 1000.0:.3f} ms")
    print(f"  Eviction elapsed: {ttl['eviction_elapsed_s'] * 1000.0:.3f} ms")

    assert ttl["status_code"] == 200, "post-TTL request stopped responding"
    assert ttl["after_size"] <= 2, f"expired keys were not cleared: {ttl['after_size']}"
    assert ttl["after_bytes"] < ttl["before_bytes"], "cache did not shrink after TTL expiry"

    concurrency = await run_concurrency_checks(middleware)
    print("\n[PHASE 3] Basic concurrency")
    print(f"  200 unique requests in parallel: {concurrency['unique_elapsed_s'] * 1000.0:.3f} ms total")
    print(f"  Parallel unique avg latency: {concurrency['unique_latency_avg_ms']:.3f} ms")
    print(f"  Same-IP concurrent requests: ok={concurrency['same_ip_ok']}, rate_limited={concurrency['same_ip_rate_limited']}")

    assert all(status == 200 for status in concurrency["unique_statuses"]), "a unique-client request failed"
    assert concurrency["same_ip_ok"] == 5, "same-IP concurrency did not preserve the limit atomically"
    assert concurrency["same_ip_rate_limited"] == 15, "same-IP concurrency did not rate-limit the overflow"

    final_current, final_peak = tracemalloc.get_traced_memory()
    print("\n[FINAL] Memory")
    print(f"  Current traced memory: {final_current / 1024:.1f} KB")
    print(f"  Peak traced memory: {final_peak / 1024:.1f} KB")

    print("\nVERDICT")
    print("- Cache remained bounded under thousands of unique clients")
    print("- Old keys expired and were removed after TTL")
    print("- Requests continued responding during burst and concurrency")
    print("- Basic same-IP concurrency preserved the limit atomically")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))