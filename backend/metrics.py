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
else:
    REQUEST_COUNT = _NoOpMetric()
    REQUEST_DURATION = _NoOpMetric()
    IN_FLIGHT = _NoOpMetric()
    ERROR_COUNT = _NoOpMetric()


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
