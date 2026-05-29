from tokdown.domain.logging.api import LogLevel, StructuredLogger


class NoOpStructuredLogger(StructuredLogger):
    def event(self, level: LogLevel, event_name: str, **context: object) -> None:
        return None
