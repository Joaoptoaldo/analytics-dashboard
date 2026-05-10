#!/usr/bin/env python
"""
Advanced cloud-like production simulation (without definitive deploy).
Covers: cold start, readiness flapping, partial dependency failure,
client timeout behavior, light concurrency/load, CORS, fail-fast startup,
metrics endpoint, token-misconfiguration behavior and structured logs.
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_PATH = BASE_DIR / "qa_cloud_advanced_report.json"
LOG_DIR = BASE_DIR / "logs"


@dataclass
class BackendProcess:
    proc: subprocess.Popen
    log_path: Path


def _parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip().strip('"').strip("'")
    return values


def _resolve_database_url() -> str | None:
    # Prefer current process env; fallback to .env for local simulation only.
    value = os.getenv("DATABASE_URL", "").strip()
    if value:
        return value

    dotenv_values = _parse_dotenv(BASE_DIR / ".env")
    return dotenv_values.get("DATABASE_URL", "").strip() or None


def _start_backend(port: int, env_overrides: dict[str, str], log_name: str) -> BackendProcess:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / log_name

    env = os.environ.copy()
    env.update(env_overrides)

    log_fp = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(BASE_DIR),
        env=env,
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return BackendProcess(proc=proc, log_path=log_path)


def _stop_backend(bp: BackendProcess) -> None:
    if bp.proc.poll() is None:
        bp.proc.terminate()
        try:
            bp.proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            bp.proc.kill()
            bp.proc.wait(timeout=5)


def _wait_status_ok(url: str, timeout_seconds: int = 45) -> tuple[bool, float]:
    started = time.perf_counter()
    deadline = started + timeout_seconds
    while time.perf_counter() < deadline:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return True, round(time.perf_counter() - started, 3)
        except Exception:
            pass
        time.sleep(0.25)
    return False, round(time.perf_counter() - started, 3)


def _status_latency(url: str, timeout: float = 8.0) -> tuple[int | None, float | None, str | None]:
    started = time.perf_counter()
    try:
        resp = requests.get(url, timeout=timeout)
        return resp.status_code, round((time.perf_counter() - started) * 1000, 2), None
    except Exception as exc:
        return None, None, exc.__class__.__name__


def _preflight(base_url: str, origin: str) -> dict[str, Any]:
    try:
        resp = requests.options(
            f"{base_url}/api/products",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
            timeout=8,
        )
        return {
            "status_code": resp.status_code,
            "allow_origin": resp.headers.get("access-control-allow-origin"),
            "allow_methods": resp.headers.get("access-control-allow-methods"),
        }
    except Exception as exc:
        return {"status_code": None, "error": exc.__class__.__name__}


def _run_load(base_url: str, total_requests: int = 60, workers: int = 20) -> dict[str, Any]:
    endpoints = [
        "/api/overview?period=30d&category=all&status=all",
        "/api/products?page=1&page_size=8&period=30d&category=all&status=all",
        "/api/sales/monthly?period=30d&category=all&status=all",
        "/api/sales/trend?range=30d&period=30d&category=all&status=all",
    ]

    def _call(i: int) -> tuple[int | None, float | None, str | None]:
        endpoint = endpoints[i % len(endpoints)]
        return _status_latency(f"{base_url}{endpoint}", timeout=10)

    latencies: list[float] = []
    status_hist: dict[str, int] = {}
    errors: dict[str, int] = {}

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(_call, i) for i in range(total_requests)]
        for fut in as_completed(futures):
            status, latency_ms, error = fut.result()
            if latency_ms is not None:
                latencies.append(latency_ms)
            if status is not None:
                key = str(status)
                status_hist[key] = status_hist.get(key, 0) + 1
            if error:
                errors[error] = errors.get(error, 0) + 1

    p50 = round(statistics.median(latencies), 2) if latencies else None
    p95 = None
    if latencies:
        sorted_vals = sorted(latencies)
        idx = int(0.95 * (len(sorted_vals) - 1))
        p95 = round(sorted_vals[idx], 2)

    return {
        "total_requests": total_requests,
        "workers": workers,
        "status_hist": status_hist,
        "errors": errors,
        "latency_ms": {
            "min": round(min(latencies), 2) if latencies else None,
            "p50": p50,
            "p95": p95,
            "max": round(max(latencies), 2) if latencies else None,
            "avg": round(sum(latencies) / len(latencies), 2) if latencies else None,
        },
    }


def _structured_log_evidence(log_path: Path) -> dict[str, Any]:
    result = {
        "json_lines": 0,
        "has_request_finished": False,
        "has_readiness_event": False,
        "has_pool_error": False,
        "sample_messages": [],
    }
    if not log_path.exists():
        return result

    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except Exception:
            continue

        result["json_lines"] += 1
        message = str(payload.get("message", ""))
        if message == "request.finished":
            result["has_request_finished"] = True
        if message.startswith("readiness") or message.startswith("health."):
            result["has_readiness_event"] = True
        if "QueuePool" in message or "too many clients" in message.lower():
            result["has_pool_error"] = True
        if len(result["sample_messages"]) < 8 and message:
            result["sample_messages"].append(message)

    return result


def _fail_fast_check_invalid_prod() -> dict[str, Any]:
    code = (
        "import os; "
        "os.environ.update({'ENV':'production','ALLOW_SEED':'false','DATABASE_URL':'sqlite:///./invalid.db',"
        "'CORS_ORIGINS':'https://app.example.com','EXTERNAL_SYNC_TOKEN':'x'*32}); "
        "import backend.main"
    )
    run = subprocess.run([sys.executable, "-c", code], cwd=str(BASE_DIR), capture_output=True, text=True)
    return {
        "exit_code": run.returncode,
        "passed": run.returncode != 0,
        "stderr_tail": (run.stderr or "")[-400:],
    }


def main() -> int:
    db_url = _resolve_database_url()
    if not db_url:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "blocked",
            "reason": "DATABASE_URL not found in env/.env for simulation",
        }
        REPORT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print("BLOCKED: DATABASE_URL not found")
        return 2

    port = 8020
    base_url = f"http://127.0.0.1:{port}"
    shared_env = {
        "ENV": "production",
        "ALLOW_SEED": "false",
        "DATABASE_URL": db_url,
        "CORS_ORIGINS": "https://dashboard-sim.vercel.app",
        "EXTERNAL_SYNC_TOKEN": "sim_token_0123456789abcdef0123456789abcdef",
        "WEB_CONCURRENCY": "1",
        "DB_POOL_SIZE": "3",
        "DB_MAX_OVERFLOW": "2",
        "DB_CONNECT_TIMEOUT_SECONDS": "5",
        "DB_STATEMENT_TIMEOUT_MS": "5000",
    }

    report: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "cloud-like-simulation-no-final-deploy",
        "checks": {},
    }

    # A) cold start + baseline runtime
    baseline = _start_backend(port, shared_env, "qa_cloud_advanced_baseline.log")
    try:
        ok, startup_s = _wait_status_ok(f"{base_url}/health", timeout_seconds=50)
        report["checks"]["cold_start"] = {
            "startup_ok": ok,
            "startup_seconds": startup_s,
        }

        # readiness flapping window
        readiness_samples: list[dict[str, Any]] = []
        for _ in range(12):
            st, lat, err = _status_latency(f"{base_url}/readiness", timeout=10)
            readiness_samples.append({"status": st, "latency_ms": lat, "error": err})
            time.sleep(0.5)

        hist: dict[str, int] = {}
        for s in readiness_samples:
            key = str(s["status"])
            hist[key] = hist.get(key, 0) + 1

        report["checks"]["readiness_flapping"] = {
            "samples": len(readiness_samples),
            "status_hist": hist,
            "sample": readiness_samples[:6],
        }

        report["checks"]["health_vs_readiness"] = {
            "health": _status_latency(f"{base_url}/health", timeout=6),
            "readiness": _status_latency(f"{base_url}/readiness", timeout=10),
            "health_ready": _status_latency(f"{base_url}/health/ready", timeout=10),
        }

        # endpoint latency and analytics
        analytics_endpoints = [
            "/api/overview?period=30d&category=all&status=all",
            "/api/products?page=1&page_size=8&period=30d&category=all&status=all",
            "/api/sales/monthly?period=30d&category=all&status=all",
            "/api/sales/trend?range=30d&period=30d&category=all&status=all",
            "/api/top/products",
        ]
        endpoint_stats = {}
        for ep in analytics_endpoints:
            endpoint_stats[ep] = _status_latency(f"{base_url}{ep}", timeout=10)

        report["checks"]["analytics_endpoint_latency"] = endpoint_stats

        report["checks"]["cors_preflight"] = _preflight(base_url, "https://dashboard-sim.vercel.app")
        report["checks"]["metrics_endpoint"] = _status_latency(f"{base_url}/metrics", timeout=6)

        # sync with missing header when token configured => 401
        try:
            sync_resp = requests.post(f"{base_url}/internal/external-products/sync", timeout=6)
            sync_status = sync_resp.status_code
        except Exception:
            sync_status = None
        report["checks"]["sync_without_header_when_token_set"] = {"status_code": sync_status}

        report["checks"]["light_concurrency"] = _run_load(base_url, total_requests=60, workers=20)
    finally:
        _stop_backend(baseline)

    # B) partial dependency failure + client timeout behavior
    degraded_env = dict(shared_env)
    degraded_env["DUMMYJSON_URL"] = "http://10.255.255.1:81/products"
    degraded = _start_backend(port, degraded_env, "qa_cloud_advanced_degraded.log")
    try:
        _wait_status_ok(f"{base_url}/health", timeout_seconds=50)

        st_hr, lat_hr, err_hr = _status_latency(f"{base_url}/health/ready", timeout=10)

        # Client-side timeout shorter than backend dependency timeout.
        started = time.perf_counter()
        timeout_error = None
        try:
            requests.get(f"{base_url}/health/ready", timeout=1)
        except Exception as exc:
            timeout_error = exc.__class__.__name__
        timeout_ms = round((time.perf_counter() - started) * 1000, 2)

        report["checks"]["partial_dependency_failure"] = {
            "health_ready_status": st_hr,
            "health_ready_latency_ms": lat_hr,
            "health_ready_error": err_hr,
            "health_status": _status_latency(f"{base_url}/health", timeout=6),
            "client_timeout_simulation": {
                "timeout_error": timeout_error,
                "elapsed_ms": timeout_ms,
            },
        }
    finally:
        _stop_backend(degraded)

    # C) behavior without EXTERNAL_SYNC_TOKEN (fail-closed)
    no_token_env = dict(shared_env)
    no_token_env.pop("EXTERNAL_SYNC_TOKEN", None)
    no_token = _start_backend(port, no_token_env, "qa_cloud_advanced_no_token.log")
    try:
        _wait_status_ok(f"{base_url}/health", timeout_seconds=50)
        try:
            resp = requests.post(f"{base_url}/internal/external-products/sync", timeout=6)
            status_without_token = resp.status_code
        except Exception:
            status_without_token = None
        report["checks"]["sync_behavior_without_configured_token"] = {
            "status_code": status_without_token,
        }
    finally:
        _stop_backend(no_token)

    # D) startup fail-fast with invalid production DATABASE_URL
    report["checks"]["startup_fail_fast_invalid_prod"] = _fail_fast_check_invalid_prod()

    # E) log evidence
    report["checks"]["structured_logs_baseline"] = _structured_log_evidence(LOG_DIR / "qa_cloud_advanced_baseline.log")
    report["checks"]["structured_logs_degraded"] = _structured_log_evidence(LOG_DIR / "qa_cloud_advanced_degraded.log")

    # Verdict heuristic
    critical_failures = []
    if not report["checks"]["cold_start"]["startup_ok"]:
        critical_failures.append("cold_start_failed")
    if report["checks"]["startup_fail_fast_invalid_prod"].get("passed") is not True:
        critical_failures.append("fail_fast_invalid_prod_not_enforced")
    if report["checks"]["sync_without_header_when_token_set"].get("status_code") != 401:
        critical_failures.append("sync_token_check_unexpected")

    report["verdict"] = "PASS_WITH_RISKS" if not critical_failures else "FAIL"
    report["critical_failures"] = critical_failures

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Advanced simulation report written: {REPORT_PATH}")
    print(f"Verdict: {report['verdict']}")

    return 0 if report["verdict"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
