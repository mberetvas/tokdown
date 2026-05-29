from pathlib import Path

from tokdown.application.ports import DocumentPart, MarkdownDocument
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
