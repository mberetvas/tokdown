from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from tokdown.application.dtos import SplitDocumentRequest, SplitDocumentResult
from tokdown.application.ports import DocumentGateway, DocumentPart
from tokdown.domain.api import ChunkSizer, DocumentSplittingDomain


class ChunkSizerFactory(Protocol):
    def create_for(self, request: SplitDocumentRequest) -> ChunkSizer:
        """Create a chunk sizer for the given request."""


@dataclass
class SplitDocumentApplication:
    document_gateway: DocumentGateway
    chunk_sizer_factory: ChunkSizerFactory
    splitting_domain: DocumentSplittingDomain

    def execute(self, request: SplitDocumentRequest) -> SplitDocumentResult:
        document = self.document_gateway.load(request.source_path)
        output_dir = request.output_dir or request.source_path.parent
        sizer = self.chunk_sizer_factory.create_for(request)
        chunks = self.splitting_domain.split(document.body, request.limit, sizer)

        part_paths: list[Path] = []
        for index, chunk_body in enumerate(chunks, start=1):
            part = DocumentPart(number=index, body=chunk_body)
            self.document_gateway.save_part(
                document,
                part,
                output_dir,
                force=request.force,
            )
            part_paths.append(output_dir / f"{document.stem}_part{index}.md")

        return SplitDocumentResult(
            source_path=request.source_path,
            output_dir=output_dir,
            part_count=len(chunks),
            part_paths=tuple(part_paths),
        )
