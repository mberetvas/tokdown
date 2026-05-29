from dataclasses import dataclass

from tokdown.domain.api import TokenEncoder

from .huggingface_encoder import HuggingFaceEncoderFactory
from .tiktoken_encoder import TiktokenEncoderFactory


class TokenEncoderFactory:
    def create(self, token_provider: str, model_id: str) -> TokenEncoder:
        raise NotImplementedError


@dataclass
class CompositeTokenEncoderFactory(TokenEncoderFactory):
    _tiktoken_factory: TiktokenEncoderFactory | None = None
    _huggingface_factory: HuggingFaceEncoderFactory | None = None

    def create(self, token_provider: str, model_id: str) -> TokenEncoder:
        if token_provider == "openai":
            factory = self._tiktoken_factory or TiktokenEncoderFactory()
            return factory.create(model_id)
        if token_provider == "google":
            factory = self._huggingface_factory or HuggingFaceEncoderFactory()
            return factory.create(model_id)
        msg = f"unsupported token provider: {token_provider}"
        raise NotImplementedError(msg)
