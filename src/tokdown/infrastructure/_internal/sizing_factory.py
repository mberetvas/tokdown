from dataclasses import dataclass

from tokdown.application.dtos import SplitDocumentRequest
from tokdown.domain.api import ChunkSizer, ChunkUnit, WordChunkSizer


@dataclass
class ChunkSizerFactory:
    def create_for(self, request: SplitDocumentRequest) -> ChunkSizer:
        if request.limit.unit == ChunkUnit.WORDS:
            return WordChunkSizer()
        msg = f"unsupported chunk unit: {request.limit.unit}"
        raise NotImplementedError(msg)
