from tokdown.domain.logging.api import LogLevel

from .sanitizer import sanitize_context


def build_log_record(
    *,
    level: LogLevel,
    event_name: str,
    correlation_id: str,
    token_provider: str,
    context: dict[str, object],
) -> dict[str, object]:
    record: dict[str, object] = {
        "level": level.value,
        "event": event_name,
        "correlation_id": correlation_id,
        "token_provider": token_provider,
    }
    record.update(sanitize_context(context))
    return record
