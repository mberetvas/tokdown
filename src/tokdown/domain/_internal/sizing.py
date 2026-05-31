from typing import Protocol


class ChunkSizer(Protocol):
    def measure(self, text: str) -> int:
        """Return the size of text in the sizer's unit."""

    def hard_split(self, text: str, limit: int) -> list[str]:
        """Split text into chunks, each at most *limit* units."""


class TokenEncoder(Protocol):
    def encode(self, text: str) -> list[int]:
        """Encode text into token ids."""

    def decode(self, token_ids: list[int]) -> str:
        """Decode token ids back into text."""


class WordChunkSizer:
    def measure(self, text: str) -> int:
        stripped = text.strip()
        if not stripped:
            return 0
        return len(stripped.split())

    def hard_split(self, text: str, limit: int) -> list[str]:
        words = text.split()
        if not words:
            return [""]
        chunks: list[str] = []
        for start in range(0, len(words), limit):
            chunks.append(" ".join(words[start : start + limit]))
        return chunks
