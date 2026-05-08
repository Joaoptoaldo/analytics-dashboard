import logging
import os
import json
from datetime import datetime
import contextvars

# Context variables para propagar por async tasks
request_id_ctx: contextvars.ContextVar = contextvars.ContextVar("request_id", default=None)
trace_id_ctx: contextvars.ContextVar = contextvars.ContextVar("trace_id", default=None)
span_id_ctx: contextvars.ContextVar = contextvars.ContextVar("span_id", default=None)


class ContextFilter(logging.Filter):
    def filter(self, record):
        # Anexa request context (request_id, trace_id, span_id) ao record se disponível
        record.request_id = request_id_ctx.get() or ""
        record.trace_id = trace_id_ctx.get() or ""
        record.span_id = span_id_ctx.get() or ""
        return True


class JSONFormatter(logging.Formatter):
    def format(self, record):
        # Base fields
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", ""),
            "trace_id": getattr(record, "trace_id", ""),
            "span_id": getattr(record, "span_id", ""),
        }

        # Optional common extras
        for key in ("route", "method", "status_code", "duration_ms", "client_ip", "exception_type", "external_dependency"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        # Exception formatting
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Merge any extra dict if provided
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            payload.update(extra)

        try:
            return json.dumps(payload, default=str, ensure_ascii=False)
        except Exception:
            # Fallback to simple message on serialization error
            return json.dumps({"timestamp": datetime.utcnow().isoformat()+"Z", "level": "ERROR", "message": "log_serialize_error"})


def configure_logging():
    """Configura logger raiz para emitir JSON no stdout, com nível configurável via env `LOG_LEVEL`."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    # Remove handlers configurados anteriormente (safety for re-imports)
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root.setLevel(level)
    root.addFilter(ContextFilter())
    root.addHandler(handler)


def set_request_id(value: str | None):
    if value is None:
        # reset to default
        request_id_ctx.set(None)
    else:
        request_id_ctx.set(str(value))


def get_request_id() -> str | None:
    return request_id_ctx.get()


def set_trace_id(value: str | None):
    if value is None:
        trace_id_ctx.set(None)
    else:
        trace_id_ctx.set(str(value))


def get_trace_id() -> str | None:
    return trace_id_ctx.get()


def set_span_id(value: str | None):
    if value is None:
        span_id_ctx.set(None)
    else:
        span_id_ctx.set(str(value))


def get_span_id() -> str | None:
    return span_id_ctx.get()
