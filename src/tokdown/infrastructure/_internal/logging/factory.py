from uuid import uuid4

from tokdown.domain.logging.api import LogLevel, StructuredLogger

from .noop_logger import NoOpStructuredLogger
from .structured_logger import JsonStructuredLogger, TextStructuredLogger


def create_structured_logger(
    *,
    log_level: LogLevel,
    log_format: str,
    correlation_id: str,
    token_provider: str,
) -> StructuredLogger:
    effective_correlation_id = correlation_id or str(uuid4())
    if log_format == "json":
        return JsonStructuredLogger(
            correlation_id=effective_correlation_id,
            token_provider=token_provider,
            minimum_level=log_level,
        )
    if log_format == "text":
        return TextStructuredLogger(
            correlation_id=effective_correlation_id,
            token_provider=token_provider,
            minimum_level=log_level,
        )
    return NoOpStructuredLogger()
