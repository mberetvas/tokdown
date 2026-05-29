from dataclasses import dataclass, field
from pathlib import Path

from tokdown.application.ports import (
    DocumentGateway,
    DocumentPart,
    MarkdownDocument,
    PartFileExistsError,
)


@dataclass
class FakeDocumentGateway(DocumentGateway):
    documents: dict[Path, str] = field(default_factory=dict)
    written_parts: list[tuple[Path, str]] = field(default_factory=list)

    def load(self, path: Path) -> MarkdownDocument:
        if path not in self.documents:
            msg = f"document not found: {path}"
            raise FileNotFoundError(msg)
        return MarkdownDocument(path=path, body=self.documents[path])

    def save_part(
        self,
        document: MarkdownDocument,
        part: DocumentPart,
        directory: Path,
        *,
        force: bool,
    ) -> None:
        part_path = directory / f"{document.stem}_part{part.number}.md"
        if part_path in {path for path, _ in self.written_parts} and not force:
            raise PartFileExistsError(f"Part file already exists: {part_path}")
        self.written_parts = [
            (path, body) for path, body in self.written_parts if path != part_path
        ]
        self.written_parts.append((part_path, part.body))
