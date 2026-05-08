import time
import logging
from starlette.responses import Response

# Try to import prometheus_client; if missing, provide no-op shim to keep app operational in environments without the package
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROM_AVAILABLE = True
except Exception:
    PROM_AVAILABLE = False


class _NoOpMetric:
    def __init__(self, *args, **kwargs):
        pass

    def labels(self, *args, **kwargs):
        return self

    def inc(self, *args, **kwargs):
        return None

    def dec(self, *args, **kwargs):
        return None

    def observe(self, *args, **kwargs):
        return None

    def set(self, *args, **kwargs):
        return None


if PROM_AVAILABLE:
    REQUEST_COUNT = Counter(
        "http_requests_total",
        "Total HTTP requests",
        ["method", "path", "status_code"],
    )
    REQUEST_DURATION = Histogram(
        "http_request_duration_seconds",
        "HTTP request latency in seconds",
        ["method", "path"],
    )
    IN_FLIGHT = Gauge("http_in_flight_requests", "In-flight HTTP requests")
    ERROR_COUNT = Counter("http_errors_total", "Total HTTP errors", ["method", "path", "status_code"])
    READINESS_STATUS = Gauge(
        "service_readiness_status",
        "Readiness status (1=ready, 0=not_ready)",
        ["endpoint"],
    )
    DEPENDENCY_STATUS = Gauge(
        "service_dependency_status",
        "Dependency status (1=healthy, 0=unhealthy)",
        ["endpoint", "dependency"],
    )
    HEALTHCHECK_DURATION = Histogram(
        "healthcheck_duration_seconds",
        "Healthcheck duration in seconds",
        ["endpoint"],
    )
else:
    REQUEST_COUNT = _NoOpMetric()
    REQUEST_DURATION = _NoOpMetric()
    IN_FLIGHT = _NoOpMetric()
    ERROR_COUNT = _NoOpMetric()
    READINESS_STATUS = _NoOpMetric()
    DEPENDENCY_STATUS = _NoOpMetric()
    HEALTHCHECK_DURATION = _NoOpMetric()


def record_readiness(endpoint: str, ready: bool, duration_ms: float | int | None = None, dependencies: dict[str, bool] | None = None) -> None:
    """Atualiza métricas operacionais de readiness/dependências sem impactar o fluxo da API."""
    try:
        READINESS_STATUS.labels(endpoint=endpoint).set(1 if ready else 0)
    except Exception:
        logging.exception("Failed to record readiness status")

    if duration_ms is not None:
        try:
            HEALTHCHECK_DURATION.labels(endpoint=endpoint).observe(max(float(duration_ms), 0.0) / 1000.0)
        except Exception:
            logging.exception("Failed to record healthcheck duration")

    if dependencies:
        for dep_name, dep_ok in dependencies.items():
            try:
                DEPENDENCY_STATUS.labels(endpoint=endpoint, dependency=dep_name).set(1 if dep_ok else 0)
            except Exception:
                logging.exception("Failed to record dependency status")


def metrics_endpoint():
    if not PROM_AVAILABLE:
        # Return a minimal text response indicating metrics disabled
        return Response(content=b"# metrics disabled (prometheus_client missing)\n", media_type="text/plain; version=0.0.4")
    try:
        data = generate_latest()
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
    except Exception:
        logging.exception("Failed to generate metrics")
        return Response(content=b"", media_type=CONTENT_TYPE_LATEST)
