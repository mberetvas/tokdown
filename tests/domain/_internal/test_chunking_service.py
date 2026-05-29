from dataclasses import dataclass, field

from tokdown.domain._internal.markdown_regions import FenceInfo
from tokdown.domain._internal.services import MarkdownChunkingService
from tokdown.domain._internal.sizing import WordChunkSizer
from tokdown.domain._internal.value_objects import ChunkLimit, ChunkUnit
from tokdown.domain.logging.api import LogEvent, LogLevel, StructuredLogger


@dataclass
class FakeStructuredLogger(StructuredLogger):
    events: list[tuple[LogLevel, str, dict[str, object]]] = field(
        default_factory=list,
    )

    def event(self, level: LogLevel, event_name: str, **context: object) -> None:
        self.events.append((level, event_name, context))


def test_oversized_python_fence_splits_with_auto_healing() -> None:
    body = "```python\none two three four five six\n```"
    limit = ChunkLimit(value=2, unit=ChunkUnit.WORDS)
    sizer = WordChunkSizer()
    logger = FakeStructuredLogger()
    service = MarkdownChunkingService(logger=logger)

    chunks = service.split(body, limit, sizer)

    assert len(chunks) == 3
    assert chunks[0].startswith("```python\n")
    assert chunks[0].endswith("\n```\n")
    assert "one two" in chunks[0]
    assert chunks[1].startswith("\n```python\n")
    assert chunks[1].endswith("\n```\n")
    assert "three four" in chunks[1]
    assert chunks[2].startswith("\n```python\n")
    assert chunks[2].endswith("\n```")
    assert "five six" in chunks[2]
    for chunk in chunks:
        assert _code_lines_are_inside_fence(chunk)


def test_healing_preserves_indent_marker_and_length() -> None:
    body = "    ~~~~bash script.sh\nalpha beta gamma delta\n    ~~~~"
    fence = FenceInfo(
        indent="    ",
        marker_char="~",
        marker_len=4,
        info_string="bash script.sh",
    )
    limit = ChunkLimit(value=2, unit=ChunkUnit.WORDS)
    service = MarkdownChunkingService()
    unit_text = body

    chunks = service.split(
        unit_text,
        limit,
        WordChunkSizer(),
    )

    assert len(chunks) == 2
    assert chunks[0].endswith("\n    ~~~~\n")
    assert chunks[1].startswith("\n    ~~~~bash script.sh\n")
    assert fence.indent in chunks[0]
    assert "~~~~" in chunks[0]


def test_hard_split_emits_code_block_hard_split_warn_event() -> None:
    body = "```python\none two three four\n```"
    logger = FakeStructuredLogger()
    service = MarkdownChunkingService(logger=logger)

    service.split(body, ChunkLimit(value=2, unit=ChunkUnit.WORDS), WordChunkSizer())

    assert len(logger.events) == 1
    level, event_name, context = logger.events[0]
    assert level is LogLevel.WARN
    assert event_name == LogEvent.CODE_BLOCK_HARD_SPLIT
    assert context["fence_language"] == "python"
    assert context["marker"] == "```"


def _code_lines_are_inside_fence(chunk: str) -> bool:
    lines = chunk.split("\n")
    fence_lines = [
        index
        for index, line in enumerate(lines)
        if line.startswith("```") or line.startswith("~~~") or "~~~~" in line
    ]
    return len(fence_lines) >= 2
