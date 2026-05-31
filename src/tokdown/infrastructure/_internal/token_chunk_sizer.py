from dataclasses import dataclass

from tokdown.domain.api import TokenEncoder


@dataclass(frozen=True)
class TokenChunkSizer:
    encoder: TokenEncoder

    def measure(self, text: str) -> int:
        if not text:
            return 0
        return len(self.encoder.encode(text))

    def hard_split(self, text: str, limit: int) -> list[str]:
        token_ids = self.encoder.encode(text)
        if not token_ids:
            return [""]
        chunks: list[str] = []
        for start in range(0, len(token_ids), limit):
            chunk_ids = token_ids[start : start + limit]
            chunks.append(self.encoder.decode(chunk_ids))
        return chunks
