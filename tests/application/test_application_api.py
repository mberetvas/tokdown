from pathlib import Path

import pytest

from tests.fakes.fake_document_gateway import FakeDocumentGateway
from tests.fakes.fake_structured_logger import FakeStructuredLogger
from tokdown.application.api import (
    CountDocumentApplication,
    CountDocumentRequest,
    PartFileExistsError,
    SizerConfig,
    SplitDocumentApplication,
    SplitDocumentRequest,
)
from tokdown.domain.api import ChunkUnit, DocumentSplittingDomain, chunk_limit
from tokdown.domain.logging.api import LogEvent, LogLevel
from tokdown.infrastructure.api import create_infrastructure


@pytest.fixture
def source_path(tmp_path: Path) -> Path:
    path = tmp_path / "notes.md"
    path.write_text("one two three\n\nfour five six", encoding="utf-8")
    return path


def test_execute_writes_part_files_via_gateway(
    source_path: Path,
    tmp_path: Path,
) -> None:
    infrastructure = create_infrastructure()
    gateway = FakeDocumentGateway(
        documents={source_path: source_path.read_text(encoding="utf-8")},
    )
    application = SplitDocumentApplication(
        document_gateway=gateway,
        chunk_sizer_factory=infrastructure.chunk_sizer_factory,
        splitting_domain=DocumentSplittingDomain(),
    )
    output_dir = tmp_path / "out"
    request = SplitDocumentRequest(
        source_path=source_path,
        limit=chunk_limit(3, ChunkUnit.WORDS),
        token_provider="",
        model_id="",
        output_dir=output_dir,
    )

    result = application.execute(request)

    assert result.part_count == 2
    assert gateway.written_parts == [
        (output_dir / "notes_part1.md", "one two three"),
        (output_dir / "notes_part2.md", "four five six"),
    ]


def test_execute_uses_real_chunk_sizer_factory(
    source_path: Path,
    tmp_path: Path,
) -> None:
    infrastructure = create_infrastructure()
    gateway = FakeDocumentGateway(
        documents={source_path: "alpha beta gamma delta"},
    )
    application = SplitDocumentApplication(
        document_gateway=gateway,
        chunk_sizer_factory=infrastructure.chunk_sizer_factory,
        splitting_domain=DocumentSplittingDomain(),
    )
    request = SplitDocumentRequest(
        source_path=source_path,
        limit=chunk_limit(2, ChunkUnit.WORDS),
        token_provider="",
        model_id="",
        output_dir=tmp_path,
    )

    result = application.execute(request)

    assert result.part_count == 2


def test_execute_raises_when_part_file_exists_without_force(
    source_path: Path,
    tmp_path: Path,
) -> None:
    infrastructure = create_infrastructure()
    gateway = FakeDocumentGateway(
        documents={source_path: source_path.read_text(encoding="utf-8")},
    )
    application = SplitDocumentApplication(
        document_gateway=gateway,
        chunk_sizer_factory=infrastructure.chunk_sizer_factory,
        splitting_domain=DocumentSplittingDomain(),
    )
    output_dir = tmp_path / "out"
    request = SplitDocumentRequest(
        source_path=source_path,
        limit=chunk_limit(3, ChunkUnit.WORDS),
        token_provider="",
        model_id="",
        output_dir=output_dir,
    )
    application.execute(request)

    with pytest.raises(PartFileExistsError):
        application.execute(request)


def test_execute_overwrites_existing_parts_with_force(
    source_path: Path,
    tmp_path: Path,
) -> None:
    infrastructure = create_infrastructure()
    gateway = FakeDocumentGateway(
        documents={source_path: "alpha beta gamma delta"},
    )
    application = SplitDocumentApplication(
        document_gateway=gateway,
        chunk_sizer_factory=infrastructure.chunk_sizer_factory,
        splitting_domain=DocumentSplittingDomain(),
    )
    output_dir = tmp_path / "out"
    base_request = SplitDocumentRequest(
        source_path=source_path,
        limit=chunk_limit(2, ChunkUnit.WORDS),
        token_provider="",
        model_id="",
        output_dir=output_dir,
    )
    application.execute(base_request)

    updated = SplitDocumentRequest(
        source_path=source_path,
        limit=chunk_limit(1, ChunkUnit.WORDS),
        token_provider="",
        model_id="",
        output_dir=output_dir,
        force=True,
    )
    result = application.execute(updated)

    assert result.part_count == 4
    assert len(gateway.written_parts) == 4


def test_execute_logs_output_file_exists_on_part_file_exists_error(
    source_path: Path,
    tmp_path: Path,
) -> None:
    infrastructure = create_infrastructure()
    gateway = FakeDocumentGateway(
        documents={source_path: source_path.read_text(encoding="utf-8")},
    )
    logger = FakeStructuredLogger()
    application = SplitDocumentApplication(
        document_gateway=gateway,
        chunk_sizer_factory=infrastructure.chunk_sizer_factory,
        splitting_domain=DocumentSplittingDomain(),
        logger=logger,
    )
    output_dir = tmp_path / "out"
    request = SplitDocumentRequest(
        source_path=source_path,
        limit=chunk_limit(3, ChunkUnit.WORDS),
        token_provider="",
        model_id="",
        output_dir=output_dir,
    )
    application.execute(request)

    with pytest.raises(PartFileExistsError):
        application.execute(request)

    assert len(logger.events) == 1
    level, event_name, context = logger.events[0]
    assert level is LogLevel.ERROR
    assert event_name == LogEvent.OUTPUT_FILE_EXISTS
    assert context["part_path"] == str(output_dir / "notes_part1.md")


def test_count_document_returns_word_count(source_path: Path) -> None:
    infrastructure = create_infrastructure()
    gateway = FakeDocumentGateway(
        documents={source_path: source_path.read_text(encoding="utf-8")},
    )
    application = CountDocumentApplication(
        document_gateway=gateway,
        chunk_sizer_factory=infrastructure.chunk_sizer_factory,
    )
    request = CountDocumentRequest(
        source_path=source_path,
        sizer_config=SizerConfig(
            unit=ChunkUnit.WORDS,
            token_provider="",
            model_id="",
        ),
    )

    result = application.execute(request)

    assert result.count == 6


def test_count_document_returns_openai_token_count(source_path: Path) -> None:
    infrastructure = create_infrastructure()
    gateway = FakeDocumentGateway(
        documents={source_path: "one two three"},
    )
    application = CountDocumentApplication(
        document_gateway=gateway,
        chunk_sizer_factory=infrastructure.chunk_sizer_factory,
    )
    request = CountDocumentRequest(
        source_path=source_path,
        sizer_config=SizerConfig(
            unit=ChunkUnit.TOKENS,
            token_provider="openai",
            model_id="cl100k_base",
        ),
    )

    result = application.execute(request)

    assert result.count == 3


def test_count_document_empty_body_returns_zero(source_path: Path) -> None:
    infrastructure = create_infrastructure()
    gateway = FakeDocumentGateway(documents={source_path: ""})
    application = CountDocumentApplication(
        document_gateway=gateway,
        chunk_sizer_factory=infrastructure.chunk_sizer_factory,
    )
    request = CountDocumentRequest(
        source_path=source_path,
        sizer_config=SizerConfig(
            unit=ChunkUnit.WORDS,
            token_provider="",
            model_id="",
        ),
    )

    result = application.execute(request)

    assert result.count == 0


def test_count_document_whitespace_only_body_returns_zero_for_words(
    source_path: Path,
) -> None:
    infrastructure = create_infrastructure()
    gateway = FakeDocumentGateway(documents={source_path: "   \n\t  \n"})
    application = CountDocumentApplication(
        document_gateway=gateway,
        chunk_sizer_factory=infrastructure.chunk_sizer_factory,
    )
    request = CountDocumentRequest(
        source_path=source_path,
        sizer_config=SizerConfig(
            unit=ChunkUnit.WORDS,
            token_provider="",
            model_id="",
        ),
    )

    result = application.execute(request)

    assert result.count == 0


def test_count_document_whitespace_only_body_openai_token_count(
    source_path: Path,
) -> None:
    infrastructure = create_infrastructure()
    body = "   \n\t  \n"
    gateway = FakeDocumentGateway(documents={source_path: body})
    application = CountDocumentApplication(
        document_gateway=gateway,
        chunk_sizer_factory=infrastructure.chunk_sizer_factory,
    )
    request = CountDocumentRequest(
        source_path=source_path,
        sizer_config=SizerConfig(
            unit=ChunkUnit.TOKENS,
            token_provider="openai",
            model_id="cl100k_base",
        ),
    )

    result = application.execute(request)

    assert result.count == 2
