from dataclasses import dataclass
from typing import Any

from tokdown.domain.api import TokenEncoder


@dataclass(frozen=True)
class TiktokenEncoder:
    _encoding: Any

    def encode(self, text: str) -> list[int]:
        return self._encoding.encode(text)

    def decode(self, token_ids: list[int]) -> str:
        return self._encoding.decode(token_ids)


class TiktokenEncoderFactory:
    def create(self, model_id: str) -> TokenEncoder:
        import tiktoken

        encoding = tiktoken.get_encoding(model_id)
        return TiktokenEncoder(encoding)
