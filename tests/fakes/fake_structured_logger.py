from dataclasses import dataclass, field

from tokdown.domain.logging.api import LogLevel, StructuredLogger


@dataclass
class FakeStructuredLogger(StructuredLogger):
    events: list[tuple[LogLevel, str, dict[str, object]]] = field(
        default_factory=list,
    )

    def event(self, level: LogLevel, event_name: str, **context: object) -> None:
        self.events.append((level, event_name, context))
