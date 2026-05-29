from dataclasses import dataclass
from pathlib import Path

from tokdown.domain.api import ChunkLimit


@dataclass(frozen=True)
class SplitDocumentRequest:
    source_path: Path
    limit: ChunkLimit
    token_provider: str
    model_id: str
    output_dir: Path | None
    force: bool = False


@dataclass(frozen=True)
class SplitDocumentResult:
    source_path: Path
    output_dir: Path
    part_count: int
    part_paths: tuple[Path, ...]
