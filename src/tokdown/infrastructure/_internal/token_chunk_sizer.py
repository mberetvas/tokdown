from dataclasses import dataclass

from tokdown.domain.api import TokenEncoder


@dataclass(frozen=True)
class TokenChunkSizer:
    encoder: TokenEncoder

    def measure(self, text: str) -> int:
        if not text:
            return 0
        return len(self.encoder.encode(text))
