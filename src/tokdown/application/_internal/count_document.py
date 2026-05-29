from dataclasses import dataclass

from tokdown.application.dtos import CountDocumentRequest, CountDocumentResult
from tokdown.application.ports import ChunkSizerFactory, DocumentGateway
from tokdown.domain.logging.api import StructuredLogger


@dataclass
class CountDocumentApplication:
    document_gateway: DocumentGateway
    chunk_sizer_factory: ChunkSizerFactory
    logger: StructuredLogger | None = None

    def execute(self, request: CountDocumentRequest) -> CountDocumentResult:
        document = self.document_gateway.load(request.source_path)
        sizer = self.chunk_sizer_factory.create_for(request.sizer_config)
        count = sizer.measure(document.body)
        return CountDocumentResult(source_path=request.source_path, count=count)
