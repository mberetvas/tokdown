from pathlib import Path

import pytest

from tests.fakes.fake_document_gateway import FakeDocumentGateway
from tokdown.application.api import SplitDocumentApplication, SplitDocumentRequest
from tokdown.domain.api import ChunkUnit, DocumentSplittingDomain, chunk_limit
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
