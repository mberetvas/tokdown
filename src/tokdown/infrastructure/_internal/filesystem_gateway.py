from pathlib import Path

from tokdown.application.ports import (
    DocumentGateway,
    DocumentPart,
    MarkdownDocument,
    PartFileExistsError,
)


class FileSystemDocumentGateway(DocumentGateway):
    def load(self, path: Path) -> MarkdownDocument:
        body = path.read_text(encoding="utf-8")
        return MarkdownDocument(path=path, body=body)

    def save_part(
        self,
        document: MarkdownDocument,
        part: DocumentPart,
        directory: Path,
        *,
        force: bool,
    ) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        part_path = directory / f"{document.stem}_part{part.number}.md"
        if part_path.exists() and not force:
            raise PartFileExistsError(
                f"Part file already exists: {part_path}",
            )
        part_path.write_text(part.body, encoding="utf-8")
