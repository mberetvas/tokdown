from typing import Protocol


class ChunkSizer(Protocol):
    def measure(self, text: str) -> int:
        """Return the size of text in the sizer's unit."""


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
