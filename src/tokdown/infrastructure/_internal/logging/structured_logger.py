import json
import sys
from dataclasses import dataclass

from tokdown.domain.logging.api import LogLevel, StructuredLogger

from .schema import build_log_record

_LEVEL_RANK = {
    LogLevel.DEBUG: 10,
    LogLevel.INFO: 20,
    LogLevel.WARN: 30,
    LogLevel.ERROR: 40,
}


def _level_enabled(event_level: LogLevel, minimum_level: LogLevel) -> bool:
    return _LEVEL_RANK[event_level] >= _LEVEL_RANK[minimum_level]


@dataclass(frozen=True)
class JsonStructuredLogger(StructuredLogger):
    correlation_id: str
    token_provider: str
    minimum_level: LogLevel = LogLevel.INFO

    def event(self, level: LogLevel, event_name: str, **context: object) -> None:
        if not _level_enabled(level, self.minimum_level):
            return
        record = build_log_record(
            level=level,
            event_name=event_name,
            correlation_id=self.correlation_id,
            token_provider=self.token_provider,
            context=context,
        )
        print(json.dumps(record, ensure_ascii=False), file=sys.stderr)


@dataclass(frozen=True)
class TextStructuredLogger(StructuredLogger):
    correlation_id: str
    token_provider: str
    minimum_level: LogLevel = LogLevel.INFO

    def event(self, level: LogLevel, event_name: str, **context: object) -> None:
        if not _level_enabled(level, self.minimum_level):
            return
        record = build_log_record(
            level=level,
            event_name=event_name,
            correlation_id=self.correlation_id,
            token_provider=self.token_provider,
            context=context,
        )
        parts = [f"{key}={value}" for key, value in record.items()]
        print(" ".join(parts), file=sys.stderr)
