from dataclasses import dataclass, field

from tokdown.application.dtos import SplitDocumentRequest
from tokdown.domain.api import ChunkSizer, ChunkUnit, WordChunkSizer

from .token_chunk_sizer import TokenChunkSizer
from .token_encoder_factory import CompositeTokenEncoderFactory, TokenEncoderFactory


@dataclass
class ChunkSizerFactory:
    _token_encoder_factory: TokenEncoderFactory = field(
        default_factory=CompositeTokenEncoderFactory,
    )

    def create_for(self, request: SplitDocumentRequest) -> ChunkSizer:
        if request.limit.unit == ChunkUnit.WORDS:
            return WordChunkSizer()
        if request.limit.unit == ChunkUnit.TOKENS:
            encoder = self._token_encoder_factory.create(
                request.token_provider,
                request.model_id,
            )
            return TokenChunkSizer(encoder)
        msg = f"unsupported chunk unit: {request.limit.unit}"
        raise NotImplementedError(msg)
