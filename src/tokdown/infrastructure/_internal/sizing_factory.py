from tokdown.application.dtos import SizerConfig
from tokdown.domain.api import ChunkSizer, ChunkUnit, WordChunkSizer

from . import huggingface_encoder, tiktoken_encoder
from .token_chunk_sizer import TokenChunkSizer


class ChunkSizerFactory:
    def create_for(self, config: SizerConfig) -> ChunkSizer:
        if config.unit == ChunkUnit.WORDS:
            return WordChunkSizer()
        if config.unit == ChunkUnit.TOKENS:
            return self._create_token_sizer(config.token_provider, config.model_id)
        msg = f"unsupported chunk unit: {config.unit}"
        raise NotImplementedError(msg)

    def _create_token_sizer(
        self, token_provider: str, model_id: str
    ) -> TokenChunkSizer:
        if token_provider == "openai":
            encoder = tiktoken_encoder.create_encoder(model_id)
        elif token_provider == "google":
            encoder = huggingface_encoder.create_encoder(model_id)
        else:
            msg = f"unsupported token provider: {token_provider}"
            raise NotImplementedError(msg)
        return TokenChunkSizer(encoder)
