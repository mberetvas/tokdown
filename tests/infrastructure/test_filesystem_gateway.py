from pathlib import Path

import pytest

from tokdown.application.ports import (
    DocumentPart,
    MarkdownDocument,
    PartFileExistsError,
)
from tokdown.infrastructure.api import create_infrastructure


def test_filesystem_gateway_reads_and_writes_utf8(tmp_path: Path) -> None:
    gateway = create_infrastructure().document_gateway
    source = tmp_path / "doc.md"
    text = "café — naïve résumé"
    source.write_text(text, encoding="utf-8")

    document = gateway.load(source)
    output_dir = tmp_path / "parts"
    gateway.save_part(
        document,
        DocumentPart(number=1, body=text),
        output_dir,
        force=False,
    )

    written = (output_dir / "doc_part1.md").read_text(encoding="utf-8")
    assert written == text
    assert document.body == text
    assert isinstance(document, MarkdownDocument)


def test_save_part_raises_when_file_exists_without_force(tmp_path: Path) -> None:
    gateway = create_infrastructure().document_gateway
    source = tmp_path / "doc.md"
    source.write_text("body", encoding="utf-8")
    document = gateway.load(source)
    output_dir = tmp_path / "parts"
    part = DocumentPart(number=1, body="first")

    gateway.save_part(document, part, output_dir, force=False)

    with pytest.raises(PartFileExistsError, match="doc_part1.md"):
        gateway.save_part(document, part, output_dir, force=False)


def test_save_part_overwrites_with_force(tmp_path: Path) -> None:
    gateway = create_infrastructure().document_gateway
    source = tmp_path / "doc.md"
    source.write_text("body", encoding="utf-8")
    document = gateway.load(source)
    output_dir = tmp_path / "parts"

    gateway.save_part(
        document,
        DocumentPart(number=1, body="first"),
        output_dir,
        force=False,
    )
    gateway.save_part(
        document,
        DocumentPart(number=1, body="second"),
        output_dir,
        force=True,
    )

    written = (output_dir / "doc_part1.md").read_text(encoding="utf-8")
    assert written == "second"
