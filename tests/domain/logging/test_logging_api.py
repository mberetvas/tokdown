from tests.fakes.fake_structured_logger import FakeStructuredLogger
from tokdown.domain.logging.api import LogEvent, LogLevel, StructuredLogger


def test_log_event_constants() -> None:
    assert LogEvent.CODE_BLOCK_HARD_SPLIT == "code_block_hard_split"
    assert LogEvent.OUTPUT_FILE_EXISTS == "output_file_exists"


def test_fake_structured_logger_records_events() -> None:
    logger: StructuredLogger = FakeStructuredLogger()
    assert isinstance(logger, StructuredLogger)

    logger.event(
        LogLevel.WARN,
        LogEvent.CODE_BLOCK_HARD_SPLIT,
        fence_language="python",
        marker="```",
    )

    fake = logger
    assert isinstance(fake, FakeStructuredLogger)
    assert len(fake.events) == 1
    level, event_name, context = fake.events[0]
    assert level is LogLevel.WARN
    assert event_name == LogEvent.CODE_BLOCK_HARD_SPLIT
    assert context == {"fence_language": "python", "marker": "```"}
