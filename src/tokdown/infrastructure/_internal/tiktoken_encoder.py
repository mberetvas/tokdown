from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TiktokenEncoder:
    _encoding: Any

    def encode(self, text: str) -> list[int]:
        return self._encoding.encode(text)

    def decode(self, token_ids: list[int]) -> str:
        return self._encoding.decode(token_ids)


def create_encoder(model_id: str) -> TiktokenEncoder:
    try:
        import tiktoken
    except ImportError:
        msg = (
            "tiktoken is required for OpenAI token counting."
            " Install it: uv add tiktoken"
        )
        raise ImportError(msg) from None

    encoding = tiktoken.get_encoding(model_id)
    return TiktokenEncoder(encoding)
