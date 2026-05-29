from abc import ABC, abstractmethod
from enum import Enum


class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class LogEvent:
    CODE_BLOCK_HARD_SPLIT = "code_block_hard_split"
    OUTPUT_FILE_EXISTS = "output_file_exists"


class StructuredLogger(ABC):
    @abstractmethod
    def event(self, level: LogLevel, event_name: str, **context: object) -> None:
        """Emit a structured log event."""


__all__ = ["LogEvent", "LogLevel", "StructuredLogger"]
