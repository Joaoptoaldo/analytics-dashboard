import os
import logging
try:
    import sentry_sdk
    from sentry_sdk.integrations.starlette import StarletteIntegration
except Exception:
    sentry_sdk = None

from backend.logging_config import get_request_id


def init_sentry():
    if not sentry_sdk:
        logging.getLogger(__name__).info("sentry-sdk not installed; skipping Sentry init")
        return

    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        logging.getLogger(__name__).info("SENTRY_DSN not configured; skipping Sentry init")
        return

    release = os.getenv("RELEASE") or os.getenv("VERSION") or None
    environment = os.getenv("ENV", "production")
    traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0"))
    profiles_sample_rate = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0"))

    def before_send(event, hint):
        try:
            # Ignore health checks
            req = event.get("request") or {}
            url = req.get("url") or req.get("url", "")
            if isinstance(url, str) and (url.endswith("/health") or url.endswith("/readiness") or url.endswith("/health/live") or url.endswith("/health/ready")):
                return None
            # Attach request_id if available
            rid = get_request_id()
            if rid:
                event.setdefault("tags", {})["request_id"] = rid
        except Exception:
            pass
        return event

    try:
        sentry_sdk.init(
            dsn=dsn,
            integrations=[StarletteIntegration()],
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            release=release,
            environment=environment,
            before_send=before_send,
        )
        logging.getLogger(__name__).info("Sentry initialized")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to initialize Sentry: {e}")
