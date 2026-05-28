import logging
import sys
from contextvars import ContextVar
import structlog
from app.core.config.settings import settings

CORRELATION_ID_VAR: ContextVar[str] = ContextVar("correlation_id", default="")
TRACE_ID_VAR: ContextVar[str] = ContextVar("trace_id", default="")

def get_correlation_id() -> str:
    return CORRELATION_ID_VAR.get()

def set_correlation_id(correlation_id: str) -> None:
    CORRELATION_ID_VAR.set(correlation_id)

def get_trace_id() -> str:
    return TRACE_ID_VAR.get()

def set_trace_id(trace_id: str) -> None:
    TRACE_ID_VAR.set(trace_id)

def add_correlation_id(logger, method_name: str, event_dict: dict) -> dict:
    correlation_id = get_correlation_id()
    trace_id = get_trace_id()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    if trace_id:
        event_dict["trace_id"] = trace_id
    return event_dict

def configure_logging() -> None:
    logging_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="YYYY-MM-DD HH:mm:ss"),
        add_correlation_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.ENVIRONMENT == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging_level),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging_level,
    )
