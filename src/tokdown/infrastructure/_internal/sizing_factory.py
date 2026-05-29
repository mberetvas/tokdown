from dataclasses import dataclass, field

from tokdown.application.dtos import SizerConfig
from tokdown.domain.api import ChunkSizer, ChunkUnit, WordChunkSizer

from .token_chunk_sizer import TokenChunkSizer
from .token_encoder_factory import CompositeTokenEncoderFactory, TokenEncoderFactory


@dataclass
class ChunkSizerFactory:
    _token_encoder_factory: TokenEncoderFactory = field(
        default_factory=CompositeTokenEncoderFactory,
    )

    def create_for(self, config: SizerConfig) -> ChunkSizer:
        if config.unit == ChunkUnit.WORDS:
            return WordChunkSizer()
        if config.unit == ChunkUnit.TOKENS:
            encoder = self._token_encoder_factory.create(
                config.token_provider,
                config.model_id,
            )
            return TokenChunkSizer(encoder)
        msg = f"unsupported chunk unit: {config.unit}"
        raise NotImplementedError(msg)
