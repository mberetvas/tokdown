from tokdown.domain._internal.services import MarkdownChunkingService
from tokdown.domain._internal.sizing import ChunkSizer, TokenEncoder, WordChunkSizer
from tokdown.domain._internal.value_objects import ChunkLimit, ChunkUnit


def chunk_limit(value: int, unit: ChunkUnit) -> ChunkLimit:
    return ChunkLimit(value=value, unit=unit)


class DocumentSplittingDomain:
    """Single entry point for splitting domain logic."""

    def __init__(
        self,
        *,
        chunking_service: MarkdownChunkingService | None = None,
    ) -> None:
        self._chunking_service = chunking_service or MarkdownChunkingService()

    def split(
        self,
        body: str,
        limit: ChunkLimit,
        sizer: ChunkSizer,
    ) -> list[str]:
        """Return chunk bodies, each within limit per sizer unit."""
        return self._chunking_service.split(body, limit, sizer)


__all__ = [
    "ChunkLimit",
    "ChunkSizer",
    "ChunkUnit",
    "DocumentSplittingDomain",
    "TokenEncoder",
    "WordChunkSizer",
    "chunk_limit",
]
