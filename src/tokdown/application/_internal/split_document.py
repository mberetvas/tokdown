from dataclasses import dataclass
from pathlib import Path

from tokdown.application.dtos import (
    SizerConfig,
    SplitDocumentRequest,
    SplitDocumentResult,
)
from tokdown.application.ports import (
    ChunkSizerFactory,
    DocumentGateway,
    DocumentPart,
    PartFileExistsError,
)
from tokdown.domain.api import DocumentSplittingDomain
from tokdown.domain.logging.api import LogEvent, LogLevel, StructuredLogger


@dataclass
class SplitDocumentApplication:
    document_gateway: DocumentGateway
    chunk_sizer_factory: ChunkSizerFactory
    splitting_domain: DocumentSplittingDomain
    logger: StructuredLogger | None = None

    def execute(self, request: SplitDocumentRequest) -> SplitDocumentResult:
        document = self.document_gateway.load(request.source_path)
        output_dir = request.output_dir or request.source_path.parent
        sizer = self.chunk_sizer_factory.create_for(
            SizerConfig(
                unit=request.limit.unit,
                token_provider=request.token_provider,
                model_id=request.model_id,
            ),
        )
        chunks = self.splitting_domain.split(document.body, request.limit, sizer)

        part_paths: list[Path] = []
        for index, chunk_body in enumerate(chunks, start=1):
            part = DocumentPart(number=index, body=chunk_body)
            part_path = output_dir / f"{document.stem}_part{index}.md"
            try:
                self.document_gateway.save_part(
                    document,
                    part,
                    output_dir,
                    force=request.force,
                )
            except PartFileExistsError:
                if self.logger is not None:
                    self.logger.event(
                        LogLevel.ERROR,
                        LogEvent.OUTPUT_FILE_EXISTS,
                        part_path=str(part_path),
                    )
                raise
            part_paths.append(part_path)

        return SplitDocumentResult(
            source_path=request.source_path,
            output_dir=output_dir,
            part_count=len(chunks),
            part_paths=tuple(part_paths),
        )
