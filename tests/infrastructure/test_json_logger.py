import json
import re

from tokdown.domain.logging.api import LogEvent, LogLevel
from tokdown.infrastructure.api import InfraSettings, create_infrastructure

_SNAKE_CASE_KEY = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


def test_json_logger_emits_schema_with_correlation_id(capsys) -> None:
    infrastructure = create_infrastructure(
        InfraSettings(
            log_level=LogLevel.DEBUG,
            log_format="json",
            correlation_id="corr-123",
            token_provider="openai",
        ),
    )

    infrastructure.logger.event(
        LogLevel.WARN,
        LogEvent.CODE_BLOCK_HARD_SPLIT,
        fence_language="python",
        marker="```",
        body="must not appear",
    )

    line = capsys.readouterr().err.strip()
    record = json.loads(line)

    assert record["correlation_id"] == "corr-123"
    assert record["token_provider"] == "openai"
    assert record["event"] == LogEvent.CODE_BLOCK_HARD_SPLIT
    assert record["level"] == LogLevel.WARN.value
    assert record["fence_language"] == "python"
    assert record["marker"] == "```"
    assert "body" not in record
    for key in record:
        assert _SNAKE_CASE_KEY.match(key)


def test_text_logger_emits_human_readable_line(capsys) -> None:
    infrastructure = create_infrastructure(
        InfraSettings(
            log_level=LogLevel.INFO,
            log_format="text",
            correlation_id="corr-456",
            token_provider="google",
        ),
    )

    infrastructure.logger.event(
        LogLevel.ERROR,
        LogEvent.OUTPUT_FILE_EXISTS,
        part_path="/tmp/sample_part1.md",
    )

    line = capsys.readouterr().err
    assert "event=output_file_exists" in line
    assert "correlation_id=corr-456" in line
    assert "token_provider=google" in line
    assert "part_path=/tmp/sample_part1.md" in line


def test_logger_respects_minimum_level(capsys) -> None:
    infrastructure = create_infrastructure(
        InfraSettings(
            log_level=LogLevel.ERROR,
            log_format="json",
            correlation_id="corr-789",
            token_provider="",
        ),
    )

    infrastructure.logger.event(
        LogLevel.WARN,
        LogEvent.CODE_BLOCK_HARD_SPLIT,
        marker="```",
    )

    assert capsys.readouterr().err == ""
